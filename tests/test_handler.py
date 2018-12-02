import unittest
from photostack import app


class TestHandlerCase(unittest.TestCase):
    def test_unsupported_http_method_gives_error_response(self):
        result = app.handler({"httpMethod": "UNSUPPORTED"}, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["headers"]["Content-Type"], "application/json")
        self.assertIn("Unsupported http method", result["body"])


if __name__ == "__main__":
    unittest.main()
