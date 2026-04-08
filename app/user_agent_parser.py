from user_agents import parse as parse_ua

def parse_user_agent(ua_string: str) -> dict:
    """
    Parse user agents string to extract device, browser and other info.
    """

    if not ua_string:
        return{
            "device": "Unknown",
            "browser": "Unknown",
            "os": "Unknown"
        }
    try:
        ua = parse_ua(ua_string)

        if ua.is_mobile:
            device = "Mobile"
        elif ua.is_tablet:
            device = "Tablet"
        elif ua.is_pc:
            device = "Desktop"
        elif ua.is_bot:
            device = "Bot"
        else:
            device = "Unknown"

        browser = ua.browser.family or "Unknown"
        os = ua.os.family or "Unknown"

        return {
            "device": device,
            "browser": browser,
            "os": os
        }
    except Exception as e:
        print(f"User agent parse error: {e}")
        return{
            "device": "Unknown",
            "browser": "Unknown",
            "os": "Unknown"
        }