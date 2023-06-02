from app import create_app
import os


app = create_app()

if __name__ == "__main__":

    # Make sure env variables are set
    if not os.environ.get("HTTPS_MODE"):
        raise RuntimeError("HTTPS_MODE not set.\n\tOptions: \"self-signed\", \"adhoc\", \"none\".")

    https_mode = os.environ.get("HTTPS_MODE").lower()
    
    if https_mode == "self-signed":
        # You should have self-signed certificates ready in the `certificate` directory.
        app.run(ssl_context=('certificate/fullchain.pem', 'certificate/cert-key.pem'))
    elif https_mode == "adhoc":
        # Mock HTTPS server
        # You need to install `pyopenssl` package to use this option
        app.run(ssl_context='adhoc')
    elif https_mode == "none":
        # HTTP server instead of HTTPS
        app.run()
    else:
        raise RuntimeError("Unknown HTTPS_MODE option.")
