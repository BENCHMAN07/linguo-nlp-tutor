"""Browser smoke test for sign-in, map navigation, and a complete level cycle."""
import json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=os.getenv("LINGUO_BASE_URL","http://127.0.0.1:8000")
bank=json.loads((ROOT/"data/questions.json").read_text(encoding="utf-8"))
answers={q["id"]:q["answer"] for q in bank if q.get("grading","auto")=="auto"}
name=f"Browser smoke {int(time.time())}"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.goto(BASE,wait_until="networkidle")
    page.locator("#name").fill(name)
    page.get_by_role("button",name="Begin").click()
    page.locator('.nav[data-view="map"]').click()
    page.locator(".node.available").first.click()
    cards=page.locator("[data-level-mode] .question")
    cards.first.wait_for()
    assert cards.count()>=8,"A lecture level should have at least eight grounded items"
    for index in range(cards.count()):
        card=cards.nth(index)
        question_id=card.get_attribute("data-qid")
        answer=answers[question_id]
        if card.locator("input").count():
            card.locator("input").fill(answer)
            card.locator("input").press("Enter")
        else:
            card.locator(f'[data-answer="{answer}"]').click()
    page.get_by_role("button",name="Evaluate level").click()
    page.get_by_text("Level score 100%",exact=False).wait_for(timeout=15000)
    print("Browser smoke passed: player created, map opened, level answered, 3-star evaluation shown.")
    browser.close()
