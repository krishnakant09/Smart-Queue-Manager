from app import app

# This is needed for Vercel
# The app variable is used by the Vercel deployment
# It needs to be in the global namespace of this module

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
