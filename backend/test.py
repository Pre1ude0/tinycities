def test_decode_jwt_token(payload):
    import jwt

    secret = "cips7V9bo6EMPjhP6AwfL40znvUnJk1y"

    decoded = jwt.decode(payload, secret, algorithms=["HS256"])

    return decoded

print(test_decode_jwt_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.hCLOJy--zboEVNxgSpv-IrcWczU28h42j4ZjxHBK8Cs"))
