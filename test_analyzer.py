from app.services.ai_analyzer import analyze_email

# Test email 1 — Job opportunity
result = analyze_email(
    subject="Backend Engineer Interview Invitation",
    sender="recruiter@google.com",
    body="Hi, we would like to invite you for a backend engineer interview next Tuesday. Please confirm your availability."
)
print("Test 1 - Job Opportunity:")
print(result)
print()

# Test email 2 — Newsletter
result2 = analyze_email(
    subject="Your weekly tech newsletter is here!",
    sender="newsletter@techdigest.com",
    body="This week in tech: AI breakthroughs, new Python releases, and cloud computing trends."
)
print("Test 2 - Newsletter:")
print(result2)
print()

# Test email 3 — Meeting
result3 = analyze_email(
    subject="Team standup tomorrow at 10am",
    sender="manager@company.com",
    body="Hey team, reminder that we have our weekly standup tomorrow at 10am. Please be on time."
)
print("Test 3 - Meeting:")
print(result3)