import openpyxl
import random
import string

# ============================================
# Test file 3: Oversized file (for Test 4)
# Uses RANDOM data per cell so .xlsx compression can't shrink it
# ============================================
wb = openpyxl.Workbook()
ws = wb.active

def random_text(length=200):
    """Generate a random string — won't compress well in .xlsx zip."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

print('Generating oversized file with random data... takes ~30-40 seconds')

for row in range(1, 1001):
    for col in range(1, 101):
        ws.cell(row=row, column=col, value=random_text(200))
    if row % 100 == 0:
        print(f'  Row {row}/1000 done...')

wb.save('uploads/test_too_big.xlsx')
print('Test file 3 created: test_too_big.xlsx — check size, should be >5MB')