from app.limiter import limiter
print("limiter.enabled =", getattr(limiter, "enabled", None))

from app.main import app
s = getattr(app.state, "limiter", None)
print("app.state.limiter exists:", s is not None)
print("app.state.limiter.enabled:", getattr(s, "enabled", None) if s else None)
