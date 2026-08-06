from pytrends.request import TrendReq
import time
pytrends = TrendReq(hl='fr-FR', tz=60)

cuisines = ['restaurant sushi', 'restaurant pizza', 'fast-food', 'restaurant burger']

for cuisine in cuisines:
    try:
        suggestions = pytrends.suggestions(keyword=cuisine)
        topics = [s for s in suggestions if s['type'] == 'Topic']
        print(f"\n{cuisine}:")
        for t in topics:
            print(f"  → mid={t['mid']}, title={t['title']}")
        if not topics:
            print("  ⚠️ Aucun Topic trouvé, inspecter toutes les suggestions:")
            for s in suggestions:
                print(f"    {s}")
    except Exception as e:
        print(f"❌ Erreur pour {cuisine}: {e}")
time.sleep(1)