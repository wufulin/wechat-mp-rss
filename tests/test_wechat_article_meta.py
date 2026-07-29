import unittest

from driver.wechat_article_meta import (
    InvalidWeChatArticleUrl,
    WeChatArticleMetadataError,
    parse_wechat_article_metadata,
    validate_wechat_article_url,
)


class WeChatArticleUrlTests(unittest.TestCase):
    def test_accepts_short_article_url(self):
        url = "https://mp.weixin.qq.com/s/ur6Yf1lZVyvcN7cbdvxBAw"
        self.assertEqual(validate_wechat_article_url(url), url)

    def test_accepts_encoded_legacy_article_url(self):
        url = (
            "https://mp.weixin.qq.com/s?"
            "__biz=MzIzNjc1NzUzMw%3D%3D&mid=123&idx=1&sn=abc"
        )
        self.assertEqual(validate_wechat_article_url(url), url)

    def test_rejects_non_wechat_host(self):
        with self.assertRaises(InvalidWeChatArticleUrl):
            validate_wechat_article_url(
                "https://mp.weixin.qq.com.example.com/s/ur6Yf1lZVyvcN7cbdvxBAw"
            )

    def test_rejects_non_https_url(self):
        with self.assertRaises(InvalidWeChatArticleUrl):
            validate_wechat_article_url(
                "http://mp.weixin.qq.com/s/ur6Yf1lZVyvcN7cbdvxBAw"
            )


class WeChatArticleMetadataTests(unittest.TestCase):
    def test_parses_current_wechat_page_variables(self):
        page_html = """
        <html>
          <head>
            <meta property="og:title" content="示例文章" />
            <meta property="og:article:author" content="示例作者" />
          </head>
          <script>
            var biz = "MzIzNjc1NzUzMw==" || "";
            var nickname = htmlDecode("量子位");
            var round_head_img =
              "http://mmbiz.qpic.cn/mmbiz_png/avatar/0?wx_fmt=png";
          </script>
        </html>
        """

        result = parse_wechat_article_metadata(
            page_html,
            "https://mp.weixin.qq.com/s/ur6Yf1lZVyvcN7cbdvxBAw",
        )

        self.assertEqual(result["title"], "示例文章")
        self.assertEqual(result["mp_info"]["mp_name"], "量子位")
        self.assertEqual(result["mp_info"]["biz"], "MzIzNjc1NzUzMw==")
        self.assertTrue(result["mp_info"]["logo"].startswith("https://"))

    def test_requires_account_name_and_valid_biz(self):
        with self.assertRaises(WeChatArticleMetadataError):
            parse_wechat_article_metadata(
                '<script>var biz = "not-base64";</script>',
                "https://mp.weixin.qq.com/s/ur6Yf1lZVyvcN7cbdvxBAw",
            )

    def test_does_not_treat_embedded_profile_card_as_publisher(self):
        embedded_profile = """
        <mp-common-profile
          data-nickname="文章中推荐的其他公众号"
          data-id="MzIzNjc1NzUzMw=="
          data-headimg="https://example.com/avatar.png">
        </mp-common-profile>
        """
        with self.assertRaises(WeChatArticleMetadataError):
            parse_wechat_article_metadata(
                embedded_profile,
                "https://mp.weixin.qq.com/s/ur6Yf1lZVyvcN7cbdvxBAw",
            )


if __name__ == "__main__":
    unittest.main()
