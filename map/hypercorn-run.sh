# hypercorn --certfile /etc/letsencrypt/live/floriscycles.com/cert.pem --keyfile /etc/letsencrypt/live/floriscycles.com/privkey.pem --ca-certs /etc/letsencrypt/live/floriscycles.com/fullchain.pem map:app --bind ':::8000'
hypercorn map:app --bind ':::8000'
