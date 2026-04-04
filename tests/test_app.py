"""Automated backend tests using the standard library unittest module."""

from pathlib import Path
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies.auth import require_roles
from app.exceptions import AuthorizationException
from app.models.user import UserRole
from app.routers.auth import get_logged_in_user, login_user, register_user
from app.routers.dashboard import get_dashboard_summary, get_dashboard_trends
from app.routers.transactions import create_transactions_in_bulk, list_transactions
from app.routers.users import delete_user, list_users, update_user_details
from app.schemas.transaction import (
    FinancialRecordCreate,
    FinancialRecordFilters,
    FinancialRecordListOptions,
    SortOrder,
    TransactionSortField,
)
from app.schemas.user import UserCreate, UserLogin, UserUpdate


class BackendTestCase(unittest.IsolatedAsyncioTestCase):
    """Route-level tests backed by a temporary SQLite database."""

    def setUp(self):
        """Create an isolated database for each test."""

        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        self.session_local = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )
        Base.metadata.create_all(bind=self.engine)
        self.db = self.session_local()

    def tearDown(self):
        """Dispose the temporary database resources."""

        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    async def register(
        self,
        username: str,
        email: str,
        password: str = "secret123",
    ):
        """Register a user through the auth route."""

        return await register_user(
            UserCreate(
                username=username,
                email=email,
                password=password,
            ),
            self.db,
        )

    async def login(self, username: str, password: str = "secret123"):
        """Log in a user through the auth route."""

        return await login_user(
            UserLogin(username=username, password=password),
            self.db,
        )

    async def bulk_create_transactions(self, admin_user, items):
        """Create multiple transactions through the transaction route."""

        payload = [FinancialRecordCreate(**item) for item in items]
        return await create_transactions_in_bulk(
            payload,
            self.db,
            admin_user,
        )

    async def test_first_registered_user_becomes_admin_and_can_log_in(self):
        """The first user should become the bootstrap admin."""

        admin_user = await self.register("admin1", "admin1@example.com")
        token = await self.login("admin1")
        me = await get_logged_in_user(admin_user)

        self.assertEqual(admin_user.role, UserRole.ADMIN)
        self.assertEqual(token.token_type, "bearer")
        self.assertTrue(token.access_token)
        self.assertEqual(me.username, "admin1")
        self.assertEqual(me.role, UserRole.ADMIN)

    async def test_admin_can_update_and_soft_delete_users(self):
        """Admin should be able to update user details and soft delete users."""

        admin_user = await self.register("admin1", "admin1@example.com")
        viewer_user = await self.register("viewer1", "viewer1@example.com")

        updated_user = await update_user_details(
            viewer_user.id,
            UserUpdate(
                email="analyst1@example.com",
                role=UserRole.ANALYST,
            ),
            self.db,
            admin_user,
        )
        delete_result = await delete_user(viewer_user.id, self.db, admin_user)
        remaining_users = await list_users(self.db, admin_user)

        self.assertEqual(updated_user.email, "analyst1@example.com")
        self.assertEqual(updated_user.role, UserRole.ANALYST)
        self.assertEqual(delete_result["message"], "User deleted successfully")
        self.assertEqual([user.username for user in remaining_users], ["admin1"])

    async def test_role_rules_and_transaction_listing_work(self):
        """Viewer should be blocked from writes and analyst should read transactions."""

        admin_user = await self.register("admin1", "admin1@example.com")
        viewer_user = await self.register("viewer1", "viewer1@example.com")

        with self.assertRaises(AuthorizationException):
            require_roles(UserRole.ADMIN)(viewer_user)

        analyst_user = await update_user_details(
            viewer_user.id,
            UserUpdate(role=UserRole.ANALYST),
            self.db,
            admin_user,
        )

        bulk_result = await self.bulk_create_transactions(
            admin_user,
            [
                {
                    "amount": 600,
                    "record_type": "expense",
                    "category": "food",
                    "record_date": "2026-02-01",
                    "description": "A",
                },
                {
                    "amount": 250,
                    "record_type": "expense",
                    "category": "travel",
                    "record_date": "2026-02-03",
                    "description": "B",
                },
                {
                    "amount": 4000,
                    "record_type": "income",
                    "category": "salary",
                    "record_date": "2026-02-05",
                    "description": "C",
                },
            ],
        )
        listing = await list_transactions(
            self.db,
            analyst_user,
            FinancialRecordFilters(),
            FinancialRecordListOptions(
                page=1,
                limit=2,
                sort_by=TransactionSortField.AMOUNT,
                sort_order=SortOrder.ASC,
            ),
        )

        self.assertEqual(bulk_result.created_count, 3)
        self.assertEqual(listing.total, 3)
        self.assertEqual(len(listing.items), 2)
        self.assertEqual(
            [str(item.amount) for item in listing.items],
            ["250.00", "600.00"],
        )

    async def test_dashboard_summary_and_trends_return_expected_totals(self):
        """Dashboard routes should aggregate transaction data correctly."""

        admin_user = await self.register("admin1", "admin1@example.com")
        await self.bulk_create_transactions(
            admin_user,
            [
                {
                    "amount": 5000,
                    "record_type": "income",
                    "category": "salary",
                    "record_date": "2026-01-05",
                    "description": "January salary",
                },
                {
                    "amount": 800,
                    "record_type": "expense",
                    "category": "rent",
                    "record_date": "2026-01-10",
                    "description": "January rent",
                },
                {
                    "amount": 600,
                    "record_type": "income",
                    "category": "freelance",
                    "record_date": "2026-02-03",
                    "description": "Freelance invoice",
                },
                {
                    "amount": 200,
                    "record_type": "expense",
                    "category": "food",
                    "record_date": "2026-02-07",
                    "description": "Food spend",
                },
            ],
        )

        summary = await get_dashboard_summary(self.db, admin_user)
        trends = await get_dashboard_trends(self.db, admin_user)

        self.assertEqual(str(summary.total_income), "5600.00")
        self.assertEqual(str(summary.total_expenses), "1000.00")
        self.assertEqual(str(summary.net_balance), "4600.00")
        self.assertEqual(len(summary.recent_activity), 4)
        self.assertEqual(
            [(item.period, str(item.net_balance)) for item in trends],
            [("2026-01", "4200.00"), ("2026-02", "400.00")],
        )

    async def test_transaction_search_matches_category_and_description(self):
        """Search should match category and description and respect soft delete."""

        admin_user = await self.register("admin1", "admin1@example.com")
        bulk_result = await self.bulk_create_transactions(
            admin_user,
            [
                {
                    "amount": 200,
                    "record_type": "expense",
                    "category": "food",
                    "record_date": "2026-03-01",
                    "description": "Lunch with client",
                },
                {
                    "amount": 150,
                    "record_type": "expense",
                    "category": "travel",
                    "record_date": "2026-03-02",
                    "description": "Food delivery during travel",
                },
                {
                    "amount": 3000,
                    "record_type": "income",
                    "category": "salary",
                    "record_date": "2026-03-03",
                    "description": "Monthly payroll",
                },
            ],
        )

        search_by_category = await list_transactions(
            self.db,
            admin_user,
            FinancialRecordFilters(search="food"),
            FinancialRecordListOptions(),
        )
        search_by_description = await list_transactions(
            self.db,
            admin_user,
            FinancialRecordFilters(search="payroll"),
            FinancialRecordListOptions(),
        )

        self.assertEqual(bulk_result.created_count, 3)
        self.assertEqual(search_by_category.total, 2)
        self.assertEqual(
            [item.category for item in search_by_category.items],
            ["travel", "food"],
        )
        self.assertEqual(search_by_description.total, 1)
        self.assertEqual(search_by_description.items[0].category, "salary")

    async def test_transaction_search_works_with_sorting_and_trims_empty_input(self):
        """Search should combine with sorting and ignore blank search values."""

        admin_user = await self.register("admin1", "admin1@example.com")
        await self.bulk_create_transactions(
            admin_user,
            [
                {
                    "amount": 450,
                    "record_type": "expense",
                    "category": "food",
                    "record_date": "2026-04-01",
                    "description": "Team dinner",
                },
                {
                    "amount": 120,
                    "record_type": "expense",
                    "category": "office",
                    "record_date": "2026-04-02",
                    "description": "Dinner snacks",
                },
                {
                    "amount": 800,
                    "record_type": "expense",
                    "category": "travel",
                    "record_date": "2026-04-03",
                    "description": "Flight booking",
                },
            ],
        )

        filtered_listing = await list_transactions(
            self.db,
            admin_user,
            FinancialRecordFilters(search=" dinner "),
            FinancialRecordListOptions(
                page=1,
                limit=10,
                sort_by=TransactionSortField.AMOUNT,
                sort_order=SortOrder.ASC,
            ),
        )
        blank_search_listing = await list_transactions(
            self.db,
            admin_user,
            FinancialRecordFilters(search=""),
            FinancialRecordListOptions(),
        )

        self.assertEqual(filtered_listing.total, 2)
        self.assertEqual(
            [str(item.amount) for item in filtered_listing.items],
            ["120.00", "450.00"],
        )
        self.assertEqual(blank_search_listing.total, 3)
