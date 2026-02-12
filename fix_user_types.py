import re

with open('backend/app/api/payment_routes.py', 'r') as f:
    content = f.read()

# Replace all ": User " with ": dict "
content = re.sub(r':\s*User\s*=\s*Depends', ': dict = Depends', content)

with open('backend/app/api/payment_routes.py', 'w') as f:
    f.write(content)

print('✅ Fixed all User type hints in payment_routes.py')
