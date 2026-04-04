"""Route and service level tests."""

from datetime import date
import tempfile
import unittest

from fastapi.security import HTTPAuthorizationCredentials

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BadRequestException,
    ConflictException,
    ResourceNotFoundException,
)
from app.core.security import create_access_token, decode_access_token
from app.db.session import Base
from app.dependencies.auth import get_current_user, require_roles
from app.models.transaction import RecordType
from app.models.user import UserRole
from app.routers.auth import get_logged_in_user, login_user, register_user
from app.routers.dashboard import (
    get_dashboard_category_totals,
    get_dashboard_summary,
    get_dashboard_totals,
    get_dashboard_trends,
    get_recent_activity,
)
from app.routers.transactions import (
    create_transaction_record,
    create_transactions_in_bulk,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)
from app.routers.users import (
    delete_user,
    list_users,
    update_user_details,
    update_user_status,
)
from app.schemas.dashboard import TrendGroupBy
from app.schemas.transaction import (
    FinancialRecordCreate,
    FinancialRecordFilters,
    FinancialRecordListOptions,
    FinancialRecordUpdate,
    SortOrder,
    TransactionSortField,
)
from app.schemas.user import UserCreate, UserLogin, UserStatusUpdate, UserUpdate
from tests.test_support import build_test_engine


class BackendRouteTestCase(unittest.IsolatedAsyncioTestCase):
    """Route-level tests backed by a temporary SQLite database."""

    def setUp(self):
        """Create an isolated database for each test."""

        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.engine, self.session_local = build_test_engine(
            self.temp_dir.name,
            "test.db",
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

    async def create_transaction(self, admin_user, **item):
        """Create a single transaction through the transaction route."""

        return await create_transaction_record(
            FinancialRecordCreate(**item),
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

    async def test_duplicate_registration_conflicts_are_rejected(self):
        """Duplicate usernames and emails should be blocked."""

        await self.register("admin1", "admin1@example.com")

        with self.assertRaises(ConflictException):
            await self.register("admin1", "another@example.com")

        with self.assertRaises(ConflictException):
            await self.register("another-user", "admin1@example.com")

    async def test_login_rejects_invalid_credentials_and_inactive_users(self):
        """Login should reject wrong passwords and inactive users."""

        admin_user = await self.register("admin1", "admin1@example.com")
        viewer_user = await self.register("viewer1", "viewer1@example.com")

        with self.assertRaises(AuthenticationException):
            await self.login("admin1", "wrong-password")

        await update_user_status(
            viewer_user.id,
            UserStatusUpdate(is_active=False),
            self.db,
            admin_user,
        )

        with self.assertRaises(AuthorizationException):
            await self.login("viewer1")

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

    async def test_admin_self_protection_blocks_self_deactivation_and_delete(self):
        """Admin should not be able to deactivate or delete their own account."""

        admin_user = await self.register("admin1", "admin1@example.com")

        with self.assertRaises(BadRequestException):
            await update_user_status(
                admin_user.id,
                UserStatusUpdate(is_active=False),
                self.db,
                admin_user,
            )

        with self.assertRaises(BadRequestException):
            await delete_user(admin_user.id, self.db, admin_user)

    async def test_missing_or_deleted_users_are_rejected_during_authentication(self):
        """Auth dependency should reject missing, invalid, and deleted users."""

        admin_user = await self.register("admin1", "admin1@example.com")
        valid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=create_access_token(admin_user.id),
        )

        resolved_user = get_current_user(valid_credentials, self.db)
        self.assertEqual(resolved_user.id, admin_user.id)

        with self.assertRaises(AuthenticationException):
            get_current_user(None, self.db)

        with self.assertRaises(AuthenticationException):
            get_current_user(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials="not-a-valid-token",
                ),
                self.db,
            )

        viewer_user = await self.register("viewer1", "viewer1@example.com")
        viewer_token = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=create_access_token(viewer_user.id),
        )
        await delete_user(viewer_user.id, self.db, admin_user)

        with self.assertRaises(AuthenticationException):
            get_current_user(viewer_token, self.db)

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

    async def test_transaction_crud_soft_delete_and_not_found_paths(self):
        """Transaction routes should support CRUD and hide soft-deleted records."""

        admin_user = await self.register("admin1", "admin1@example.com")
        created_transaction = await self.create_transaction(
            admin_user,
            amount="875.50",
            record_type="expense",
            category="office",
            record_date="2026-03-04",
            description="Office chair",
        )
        fetched_transaction = await get_transaction(
            created_transaction.id,
            self.db,
            admin_user,
        )
        updated_transaction = await update_transaction(
            created_transaction.id,
            FinancialRecordUpdate(
                amount="900.00",
                description="Office chair and desk lamp",
            ),
            self.db,
            admin_user,
        )
        delete_result = await delete_transaction(
            created_transaction.id,
            self.db,
            admin_user,
        )
        remaining_listing = await list_transactions(
            self.db,
            admin_user,
            FinancialRecordFilters(),
            FinancialRecordListOptions(),
        )

        self.assertEqual(fetched_transaction.id, created_transaction.id)
        self.assertEqual(str(updated_transaction.amount), "900.00")
        self.assertEqual(delete_result["message"], "Transaction deleted successfully")
        self.assertEqual(remaining_listing.total, 0)

        with self.assertRaises(ResourceNotFoundException):
            await get_transaction(created_transaction.id, self.db, admin_user)

        with self.assertRaises(ResourceNotFoundException):
            await update_transaction(
                9999,
                FinancialRecordUpdate(description="missing"),
                self.db,
                admin_user,
            )

        with self.assertRaises(ResourceNotFoundException):
            await delete_transaction(9999, self.db, admin_user)

    async def test_transaction_list_rejects_invalid_date_range_and_applies_filters(self):
        """Transaction listing should reject bad ranges and honor exact filters."""

        admin_user = await self.register("admin1", "admin1@example.com")
        await self.bulk_create_transactions(
            admin_user,
            [
                {
                    "amount": 5000,
                    "record_type": "income",
                    "category": "salary",
                    "record_date": "2026-01-05",
                    "description": "Salary",
                },
                {
                    "amount": 125,
                    "record_type": "expense",
                    "category": "food",
                    "record_date": "2026-01-07",
                    "description": "Lunch",
                },
                {
                    "amount": 90,
                    "record_type": "expense",
                    "category": "food",
                    "record_date": "2026-02-01",
                    "description": "Snacks",
                },
            ],
        )

        filtered_listing = await list_transactions(
            self.db,
            admin_user,
            FinancialRecordFilters(
                record_type=RecordType.EXPENSE,
                category="food",
                date_from=date(2026, 1, 1),
                date_to=date(2026, 1, 31),
            ),
            FinancialRecordListOptions(),
        )

        self.assertEqual(filtered_listing.total, 1)
        self.assertEqual(filtered_listing.items[0].description, "Lunch")

        with self.assertRaises(BadRequestException):
            await list_transactions(
                self.db,
                admin_user,
                FinancialRecordFilters(
                    date_from=date(2026, 3, 10),
                    date_to=date(2026, 3, 1),
                ),
                FinancialRecordListOptions(),
            )

    async def test_dashboard_summary_and_enhanced_routes_return_expected_totals(self):
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

        totals = await get_dashboard_totals(self.db, admin_user)
        category_totals = await get_dashboard_category_totals(self.db, admin_user)
        recent_activity = await get_recent_activity(self.db, admin_user, limit=2)
        summary = await get_dashboard_summary(self.db, admin_user)
        monthly_trends = await get_dashboard_trends(
            self.db,
            admin_user,
            group_by=TrendGroupBy.MONTHLY,
        )
        weekly_trends = await get_dashboard_trends(
            self.db,
            admin_user,
            group_by=TrendGroupBy.WEEKLY,
        )

        self.assertEqual(str(totals.total_income), "5600.00")
        self.assertEqual(str(totals.total_expenses), "1000.00")
        self.assertEqual(str(totals.net_balance), "4600.00")
        self.assertEqual(str(summary.total_income), "5600.00")
        self.assertEqual(str(summary.total_expenses), "1000.00")
        self.assertEqual(str(summary.net_balance), "4600.00")
        self.assertEqual(len(summary.recent_activity), 4)
        self.assertEqual(len(recent_activity), 2)
        self.assertEqual(recent_activity[0].category, "food")
        self.assertEqual(
            [(item.category, str(item.total)) for item in category_totals],
            [
                ("salary", "5000.00"),
                ("rent", "800.00"),
                ("freelance", "600.00"),
                ("food", "200.00"),
            ],
        )
        self.assertEqual(
            [(item.period, str(item.net_balance)) for item in monthly_trends],
            [("2026-01", "4200.00"), ("2026-02", "400.00")],
        )
        self.assertEqual(
            [(item.period, str(item.net_balance)) for item in weekly_trends],
            [("2026-W02", "4200.00"), ("2026-W06", "400.00")],
        )

    async def test_dashboard_handles_empty_state_and_deleted_transactions(self):
        """Dashboard routes should ignore deleted data and handle an empty database."""

        admin_user = await self.register("admin1", "admin1@example.com")

        empty_totals = await get_dashboard_totals(self.db, admin_user)
        empty_summary = await get_dashboard_summary(self.db, admin_user)
        empty_trends = await get_dashboard_trends(
            self.db,
            admin_user,
            group_by=TrendGroupBy.MONTHLY,
        )

        self.assertEqual(str(empty_totals.total_income), "0.00")
        self.assertEqual(str(empty_totals.total_expenses), "0.00")
        self.assertEqual(str(empty_totals.net_balance), "0.00")
        self.assertEqual(empty_summary.category_totals, [])
        self.assertEqual(empty_summary.recent_activity, [])
        self.assertEqual(empty_trends, [])

        created_transaction = await self.create_transaction(
            admin_user,
            amount="100.00",
            record_type="expense",
            category="food",
            record_date="2026-04-01",
            description="Temporary row",
        )
        await delete_transaction(created_transaction.id, self.db, admin_user)

        totals_after_delete = await get_dashboard_totals(self.db, admin_user)
        recent_activity_after_delete = await get_recent_activity(
            self.db,
            admin_user,
            limit=10,
        )

        self.assertEqual(str(totals_after_delete.total_expenses), "0.00")
        self.assertEqual(recent_activity_after_delete, [])

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

    def test_access_token_helpers_round_trip_and_reject_invalid_tokens(self):
        """Security helpers should decode valid tokens and reject invalid ones."""

        token = create_access_token(user_id=42)

        self.assertEqual(decode_access_token(token), 42)
        self.assertIsNone(decode_access_token("broken-token"))
