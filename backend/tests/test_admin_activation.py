
from types import SimpleNamespace

import pytest

from app.models.user import AccountOrigin, AccountStatus, UserRole
from app.services.admin_activation import AdminActivationService


def make_user(
    role=UserRole.COMPANY_ADMIN,
    origin=AccountOrigin.REGISTRATION,
    status=AccountStatus.PENDING_ACTIVATION,
):
    return SimpleNamespace(
        role=role,
        account_origin=origin,
        account_status=status,
    )


def test_initial_company_admin_is_eligible():
    user = make_user()

    assert AdminActivationService._is_eligible_user(user) is True


@pytest.mark.parametrize(
    "user",
    [
        make_user(origin=AccountOrigin.INVITATION),
        make_user(origin=AccountOrigin.OWNER_PROVISIONING),
        make_user(role=UserRole.HR),
        make_user(role=UserRole.MANAGER),
        make_user(role=UserRole.EMPLOYEE),
        make_user(status=AccountStatus.ACTIVE),
        make_user(status=AccountStatus.SUSPENDED),
        make_user(status=AccountStatus.DEACTIVATED),
        None,
    ],
)
def test_ineligible_accounts_are_rejected(user):
    assert AdminActivationService._is_eligible_user(user) is False
