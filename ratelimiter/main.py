from pulsefire.ratelimiters import RiotAPIRateLimiter

if __name__ == '__main__':
    RiotAPIRateLimiter().serve(host='0.0.0.0', port=12227)
