# get_password_simple.py
import asyncio
import json
from playwright.async_api import async_playwright

async def get_login_payload(username, password):
    final_payload = None
    
    async with async_playwright() as p:
        # 去掉 channel="msedge"，使用Playwright自带浏览器
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        captured_payloads = []
        
        async def capture_request_handler(request):
            if request.method == "POST" and "login" in request.url:
                payload = request.post_data
                try:
                    captured_payloads.append(json.loads(payload))
                except (json.JSONDecodeError, TypeError):
                    captured_payloads.append(payload)
        
        page.on("request", capture_request_handler)
        
        try:
            await page.goto("https://webvpn.nankai.edu.cn/", timeout=60000)
            await page.get_by_placeholder("请输入学号/工号").fill("99999")
            await page.get_by_placeholder("请输入密码").fill(password)
            
            form_container = page.locator("div.arco-tabs-content-item-active")
            login_button_locator = form_container.locator("button.arco-btn-primary")
            await login_button_locator.click()
            
            agree_button = page.get_by_role("button", name="同意")
            await agree_button.wait_for(state='visible', timeout=10000)
            await agree_button.click()
            
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f'❌ 操作过程中发生错误: {e}')
        finally:
            await browser.close()
            if captured_payloads:
                final_payload = captured_payloads[0]
    
    return final_payload

async def main():
    username = "2311990"
    password = "Nk20051205"  # 你的密码
    
    payload = await get_login_payload(username, password)
    
    if isinstance(payload, dict) and 'password' in payload:
        print(payload['password'])
    else:
        print("未能捕获到加密密码")

if __name__ == "__main__":
    asyncio.run(main())