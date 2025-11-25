"""Test cases with realistic git diffs for PR review evaluation."""

from pydantic_evals import Case


TEST_CASES = [
    Case(
        name='security_vulnerability',
        inputs='Review PR #101',
        metadata={
            'pr_number': 101,
            'title': 'Add user authentication',
            'diff': """diff --git a/auth/login.py b/auth/login.py
index 1234567..abcdefg 100644
--- a/auth/login.py
+++ b/auth/login.py
@@ -5,8 +5,12 @@ from database import users_table
 
 def authenticate_user(username: str, password: str) -> bool:
-    user = users_table.find_one({"username": username})
-    return user and user['password'] == password
+    \"\"\"Authenticate user with username and password.\"\"\"
+    query = f"SELECT * FROM users WHERE username='{username}'"
+    user = db.execute(query).fetchone()
+    
+    if user and user['password'] == password:
+        return True
+    return False
 
 def login_endpoint(request):
     username = request.form['username']""",
            'expected_issues': ['SQL injection', 'plaintext password comparison']
        }
    ),
    
    Case(
        name='missing_tests',
        inputs='Review PR #102',
        metadata={
            'pr_number': 102,
            'title': 'Add payment processing',
            'diff': """diff --git a/payment/processor.py b/payment/processor.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/payment/processor.py
@@ -0,0 +1,25 @@
+from decimal import Decimal
+from stripe import Charge
+
+class PaymentProcessor:
+    def __init__(self, api_key: str):
+        self.api_key = api_key
+    
+    def process_payment(self, amount: float, currency: str, card_token: str):
+        \"\"\"Process a payment through Stripe.\"\"\"
+        charge = Charge.create(
+            amount=int(amount * 100),
+            currency=currency,
+            source=card_token,
+            api_key=self.api_key
+        )
+        return charge.id
+    
+    def refund_payment(self, charge_id: str):
+        \"\"\"Refund a previous charge.\"\"\"
+        refund = Charge.refund(
+            charge_id=charge_id,
+            api_key=self.api_key
+        )
+        return refund.id""",
            'expected_issues': ['no tests', 'no error handling', 'float for money']
        }
    ),
    
    Case(
        name='good_pr_with_tests',
        inputs='Review PR #103',
        metadata={
            'pr_number': 103,
            'title': 'Fix edge case in date parsing',
            'diff': """diff --git a/utils/date_parser.py b/utils/date_parser.py
index 1234567..abcdefg 100644
--- a/utils/date_parser.py
+++ b/utils/date_parser.py
@@ -10,7 +10,10 @@ def parse_date(date_string: str) -> datetime:
     try:
         return datetime.strptime(date_string, '%Y-%m-%d')
     except ValueError:
-        raise ValueError(f"Invalid date format: {date_string}")
+        # Handle ISO 8601 format as fallback
+        try:
+            return datetime.fromisoformat(date_string)
+        except ValueError:
+            raise ValueError(f"Invalid date format: {date_string}")
 
 def format_date(date: datetime) -> str:
     return date.strftime('%Y-%m-%d')
diff --git a/tests/test_date_parser.py b/tests/test_date_parser.py
index 9876543..fedcba9 100644
--- a/tests/test_date_parser.py
+++ b/tests/test_date_parser.py
@@ -15,6 +15,14 @@ def test_parse_standard_format():
     result = parse_date('2024-01-15')
     assert result == datetime(2024, 1, 15)
 
+def test_parse_iso_format():
+    \"\"\"Test parsing ISO 8601 format with time.\"\"\"
+    result = parse_date('2024-01-15T10:30:00')
+    assert result == datetime(2024, 1, 15, 10, 30, 0)
+
+def test_parse_iso_format_with_timezone():
+    result = parse_date('2024-01-15T10:30:00+00:00')
+    assert result.year == 2024
+
 def test_parse_invalid_format():
     with pytest.raises(ValueError, match="Invalid date format"):
         parse_date('not-a-date')""",
            'expected_issues': []  # This is a good PR
        }
    ),
    
    Case(
        name='breaking_changes',
        inputs='Review PR #104',
        metadata={
            'pr_number': 104,
            'title': 'Refactor API response format',
            'diff': """diff --git a/api/views.py b/api/views.py
index 1234567..abcdefg 100644
--- a/api/views.py
+++ b/api/views.py
@@ -20,10 +20,12 @@ def get_user(user_id: int):
     if not user:
         return {'error': 'User not found'}, 404
     
-    return {
-        'id': user.id,
-        'name': user.name,
-        'email': user.email
-    }
+    return {'data': {
+        'type': 'user',
+        'id': str(user.id),
+        'attributes': {
+            'name': user.name,
+            'email': user.email
+        }
+    }}""",
            'expected_issues': ['breaking change', 'no migration guide', 'no version bump']
        }
    ),
    
    Case(
        name='performance_improvement',
        inputs='Review PR #105',
        metadata={
            'pr_number': 105,
            'title': 'Optimise database queries',
            'diff': """diff --git a/models/user.py b/models/user.py
index 1234567..abcdefg 100644
--- a/models/user.py
+++ b/models/user.py
@@ -30,12 +30,10 @@ class User(Base):
     def get_with_posts(cls, user_id: int):
         \"\"\"Get user with all their posts.\"\"\"
         user = session.query(cls).filter_by(id=user_id).first()
-        posts = session.query(Post).filter_by(user_id=user_id).all()
-        user.posts = posts
-        return user
+        return session.query(cls).options(
+            joinedload(cls.posts)
+        ).filter_by(id=user_id).first()
     
     @classmethod
     def get_active_users(cls):
-        users = session.query(cls).all()
-        return [u for u in users if u.is_active]
+        return session.query(cls).filter_by(is_active=True).all()""",
            'expected_issues': []  # This is good, but should ask about benchmarks
        }
    ),
]

