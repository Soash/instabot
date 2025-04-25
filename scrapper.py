import json
from playwright.async_api import async_playwright

COOKIES_FILE = "cookies.json"

async def check_if_liked(username: str, post_url: str) -> bool:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Load cookies from file
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)

        # Fix 'sameSite' attribute if necessary
        for cookie in cookies:
            if 'sameSite' not in cookie or cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                cookie['sameSite'] = 'Lax'

        # Add cookies to the context
        await context.add_cookies(cookies)

        # Open a new page and go to the post URL
        page = await context.new_page()
        await page.goto(f"{post_url}liked_by/")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(10000)

        # Extract the list of usernames who liked the post
        links = await page.query_selector_all("a")
        link_texts = [await link.text_content() for link in links]
        link_texts = [text.strip() for text in link_texts if text and text.strip()]

        # Save updated cookies back to the file
        cookies = await context.cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)

        # Close the browser
        await browser.close()

        # Return whether the username is in the list of users who liked the post
        return username.lower() in (name.lower() for name in link_texts)


