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

public class MainActivity extends Activity {

    private final int BG = Color.rgb(8, 7, 19);
    private final int PANEL = Color.rgb(21, 19, 41);
    private final int PURPLE = Color.rgb(131, 30, 255);
    private LinearLayout messages;
    private ScrollView scroll;

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
        root.addView(title, new LinearLayout.LayoutParams(
                -1, dp(42)));

        TextView subtitle = new TextView(this);
        subtitle.setText("دستیار هوشمند شما • رابط چت آزمایشی");
        subtitle.setTextColor(Color.LTGRAY);
        subtitle.setTextSize(12);
        subtitle.setGravity(Gravity.CENTER);
        root.addView(subtitle, new LinearLayout.LayoutParams(
                -1, dp(30)));

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
                new LinearLayout.LayoutParams( -1, 0, 1);
        root.addView(scroll, scrollParams);

        addMessage("HAMED AI CODER",
                "سلام! من دستیار هوشمند شما هستم. رابط چت آماده است. اتصال به موتور هوش مصنوعی در مرحله بعد فعال می‌شود.",
                false);

        LinearLayout composer = new LinearLayout(this);
        composer.setOrientation(LinearLayout.HORIZONTAL);
        composer.setGravity(Gravity.CENTER_VERTICAL);
        composer.setPadding(0, dp(10), 0, 0);

        EditText input = new EditText(this);
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
        inputParams.setMargins(0, 0, 0, 0);
        composer.addView(input, inputParams);

        Button send = new Button(this);
        send.setText("ارسال");
        send.setTextColor(Color.WHITE);
        send.setTextSize(13);
        send.setAllCaps(false);
        send.setBackground(round(PURPLE, 16));

        LinearLayout.LayoutParams sendParams =
                new LinearLayout.LayoutParams(dp(82), dp(50));
        sendParams.setMargins(dp(8), 0, 0, 0);
        composer.addView(send, sendParams);

        send.setOnClickListener(v -> {
            String message = input.getText().toString().trim();

            if (message.isEmpty()) {
                return;
            }

            addMessage("شما", message, true);
            input.setText("");

            addMessage("HAMED AI CODER",
                    "پیام در رابط ثبت شد؛ اتصال به موتور هوش مصنوعی در مرحله بعد فعال می‌شود.",
                    false);
        });

        root.addView(composer);
        setContentView(root);
    }

    private void addMessage(String sender, String message, boolean user) {
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
                new LinearLayout.LayoutParams(
                        -1, -2);
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
