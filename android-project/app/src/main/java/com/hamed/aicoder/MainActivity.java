package com.hamed.aicoder;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.TextView;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setBackgroundColor(Color.rgb(8, 7, 19));

        TextView title = new TextView(this);
        title.setText("HAMED AI CODER");
        title.setTextSize(28);
        title.setTextColor(Color.rgb(131, 30, 255));
        title.setGravity(Gravity.CENTER);

        TextView subtitle = new TextView(this);
        subtitle.setText("Android APK Build Test");
        subtitle.setTextSize(16);
        subtitle.setTextColor(Color.WHITE);
        subtitle.setGravity(Gravity.CENTER);

        layout.addView(title);
        layout.addView(subtitle);
        setContentView(layout);
    }
}
