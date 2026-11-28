import asyncio
import sys
sys.path.insert(0, '/home/ubuntu/hsn_agent_system')
from agents.outreach_agent import OutreachAgent

async def main():
    config = {
        "batch_size": 20,
        "channels": {
            "instagram": True,
            "whatsapp": True,
            "email": True,
            "facebook": True
        },
        "daily_limits": {
            "instagram": 50,
            "whatsapp": 30,
            "email": 100,
            "facebook": 20
        },
        "min_delay_seconds": 30,
        "max_delay_seconds": 120
    }
    agent = OutreachAgent(config)
    results = await agent.send_batch([
        {'lead_id': 'LTEST001', 'company_name': 'Artistry BJJ', 'email': 'contact@artistrybjj.com', 'channel': 'email'},
        {'lead_id': 'LTEST002', 'company_name': 'Inspire Jiu-Jitsu Academy', 'email': 'info@inspirejiujitsuacademy.com', 'channel': 'email'},
        {'lead_id': 'LTEST003', 'company_name': 'Grappling Zone', 'email': 'info@grapplingzone.com', 'channel': 'email'},
        {'lead_id': 'LTEST004', 'company_name': 'Pablo Silva Brazilian Jiu Jitsu HQ', 'email': 'info@pablosilvabjj.com', 'channel': 'email'},
        {'lead_id': 'LTEST005', 'company_name': 'Inevat Jiu Jitsu East Downtown', 'email': 'david@inevateastdowntown.com', 'channel': 'email'},
    ], channel='email', test_mode=True)
    print(f"Results: {results}")

if __name__ == '__main__':
    asyncio.run(main())