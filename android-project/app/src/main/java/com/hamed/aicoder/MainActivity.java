package com.hamed.aicoder;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    private final int BG = Color.rgb(8, 7, 19);
    private final int PANEL = Color.rgb(21, 19, 41);
    private final int PURPLE = Color.rgb(131, 30, 255);

    private static final String API_URL =
            "http://127.0.0.1:8765/chat";

    private static final String APP_KEY =
            "HAMED-LOCAL-APP-2026";

    private LinearLayout messages;
    private ScrollView scroll;
    private Button send;
    private EditText input;

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        root.setBackgroundColor(BG);
        root.setPadding(dp(16), dp(12), dp(16), dp(12));

        TextView title = new TextView(this);
        title.setText("HAMED AI CODER");
        title.setTextColor(Color.WHITE);
        title.setTextSize(23);
        title.setTypeface(null, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);

        root.addView(title, new LinearLayout.LayoutParams(-1, dp(42)));

        TextView subtitle = new TextView(this);
        subtitle.setText("دستیار هوشمند شما • متصل به هوش مصنوعی");
        subtitle.setTextColor(Color.LTGRAY);
        subtitle.setTextSize(12);
        subtitle.setGravity(Gravity.CENTER);

        root.addView(subtitle, new LinearLayout.LayoutParams(-1, dp(30)));

        View line = new View(this);
        line.setBackgroundColor(PURPLE);

        LinearLayout.LayoutParams lineParams =
                new LinearLayout.LayoutParams(-1, dp(1));
        lineParams.setMargins(0, dp(8), 0, dp(12));
        root.addView(line, lineParams);

        scroll = new ScrollView(this);
        scroll.setFillViewport(true);

        messages = new LinearLayout(this);
        messages.setOrientation(LinearLayout.VERTICAL);
        messages.setPadding(dp(4), dp(8), dp(4), dp(8));
        scroll.addView(messages);

        LinearLayout.LayoutParams scrollParams =
                new LinearLayout.LayoutParams(-1, 0, 1);
        root.addView(scroll, scrollParams);

        addMessage("HAMED AI CODER",
                "سلام! اتصال به موتور هوش مصنوعی آماده آزمایش است.",
                false);

        LinearLayout composer = new LinearLayout(this);
        composer.setOrientation(LinearLayout.HORIZONTAL);
        composer.setGravity(Gravity.CENTER_VERTICAL);
        composer.setPadding(0, dp(10), 0, 0);

        input = new EditText(this);
        input.setSingleLine(true);
        input.setTextSize(14);
        input.setTextColor(Color.WHITE);
        input.setHintTextColor(Color.GRAY);
        input.setHint("پیامت را بنویس...");
        input.setPadding(dp(12), 0, dp(12), 0);
        input.setBackground(round(PANEL, 18));
        input.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        LinearLayout.LayoutParams inputParams =
                new LinearLayout.LayoutParams(0, dp(50), 1);
        composer.addView(input, inputParams);

        send = new Button(this);
        send.setText("ارسال");
        send.setTextColor(Color.WHITE);
        send.setTextSize(13);
        send.setAllCaps(false);
        send.setBackground(round(PURPLE, 16));

        LinearLayout.LayoutParams sendParams =
                new LinearLayout.LayoutParams(dp(82), dp(50));
        sendParams.setMargins(dp(8), 0, 0, 0);
        composer.addView(send, sendParams);

        send.setOnClickListener(v -> sendMessage());

        root.addView(composer);
        setContentView(root);
    }

    private void sendMessage() {
        String message = input.getText().toString().trim();

        if (message.isEmpty() || !send.isEnabled()) {
            return;
        }

        addMessage("شما", message, true);
        input.setText("");

        send.setEnabled(false);
        send.setText("...");

        executor.execute(() -> {
            HttpURLConnection connection = null;

            try {
                JSONObject request = new JSONObject();
                request.put("message", message);

                String sessionId = getSharedPreferences(
                        "hamed_ai", MODE_PRIVATE
                ).getString("session_id", null);

                if (sessionId != null) {
                    request.put("session_id", sessionId);
                }

                URL url = new URL(API_URL);
                connection = (HttpURLConnection) url.openConnection();

                connection.setRequestMethod("POST");
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(60000);
                connection.setDoOutput(true);

                connection.setRequestProperty(
                        "Content-Type", "application/json; charset=UTF-8"
                );

                connection.setRequestProperty(
                        "X-Local-App-Key", APP_KEY
                );

                byte[] body = request.toString().getBytes(
                        StandardCharsets.UTF_8
                );

                try (OutputStream output = connection.getOutputStream()) {
                    output.write(body);
                }

                int status = connection.getResponseCode();

                InputStream stream = status >= 200 && status < 300
                        ? connection.getInputStream()
                        : connection.getErrorStream();

                StringBuilder result = new StringBuilder();

                if (stream != null) {
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(
                                    stream, StandardCharsets.UTF_8
                            ))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            result.append(line);
                        }
                    }
                }

                JSONObject response = new JSONObject(result.toString());

                if (status < 200 || status >= 300) {
                    throw new Exception(
                            response.optString(
                                    "error", "خطای ارتباط با سرور"
                            )
                    );
                }

                String reply = response.optString(
                        "reply", "پاسخی دریافت نشد."
                );

                String newSession = response.optString(
                        "session_id", ""
                );

                if (!newSession.isEmpty()) {
                    getSharedPreferences(
                            "hamed_ai", MODE_PRIVATE
                    ).edit().putString(
                            "session_id", newSession
                    ).apply();
                }

                runOnUiThread(() -> {
                    addMessage("HAMED AI CODER", reply, false);
                    send.setEnabled(true);
                    send.setText("ارسال");
                });

            } catch (Exception e) {
                String error = e.getMessage();

                if (error == null || error.isEmpty()) {
                    error = "ارتباط با API برقرار نشد.";
                }

                final String finalError = error;

                runOnUiThread(() -> {
                    addMessage(
                            "خطای اتصال",
                            finalError,
                            false
                    );
                    send.setEnabled(true);
                    send.setText("ارسال");
                });

            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
        });
    }

    private void addMessage(
            String sender, String message, boolean user
    ) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(10), dp(14), dp(10));
        card.setBackground(round(user ? 0xFF292044 : PANEL, 16));

        TextView name = new TextView(this);
        name.setText(sender);
        name.setTextColor(user ? 0xFFD6B5FF : 0xFFB77CFF);
        name.setTextSize(12);
        name.setTypeface(null, Typeface.BOLD);

        TextView body = new TextView(this);
        body.setText(message);
        body.setTextColor(Color.WHITE);
        body.setTextSize(14);
        body.setGravity(Gravity.RIGHT);
        body.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
        body.setPadding(0, dp(6), 0, 0);

        card.addView(name);
        card.addView(body);

        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, 0, 0, dp(12));

        messages.addView(card, params);
        scroll.post(() -> scroll.fullScroll(View.FOCUS_DOWN));
    }

    private GradientDrawable round(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radius));
        return drawable;
    }

    private int dp(int value) {
        return (int) (value * getResources()
                .getDisplayMetrics().density + 0.5f);
    }
}
