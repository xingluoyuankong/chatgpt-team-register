#!/usr/bin/env python3
import random
import string

def gen_pwd():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=16))

with open('registered_emails.txt') as f:
    emails = [line.strip() for line in f if line.strip()]

with open('final_accounts.txt', 'w') as f:
    for email in emails:
        pwd = gen_pwd()
        f.write(f"{email}----{pwd}\n")

print(f"导出完成: {len(emails)} 个账号")
print("文件: final_accounts.txt")
