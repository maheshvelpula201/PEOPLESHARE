from app.db.session import SessionLocal
from app.schemas.company import CompanyRegistrationRequest
from app.services.companies import CompanyService


db = SessionLocal()

try:
    registration = CompanyRegistrationRequest(
        company_name="PeopleSphere Test Company",
        admin_email="admin@peoplesphere-test.com",
        password="StrongTestPassword123!",
        timezone_name="Asia/Kolkata",
    )

    response = CompanyService.register_company(
        db=db,
        registration=registration,
    )

    print("\nCompany registration successful!")
    print("Company ID:", response.company_id)
    print("Company name:", response.company_name)
    print("Company slug:", response.company_slug)
    print("Company status:", response.company_status)
    print("Admin user ID:", response.admin_user_id)
    print("Admin email:", response.admin_email)
    print("Admin role:", response.admin_role)
    print("Admin account status:", response.admin_account_status)

except Exception as error:
    print("\nRegistration failed!")
    print(type(error).__name__, error)

finally:
    db.close()