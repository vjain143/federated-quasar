package com.example.teamsync.service;

import com.example.teamsync.util.ConfigService;

import jakarta.mail.*;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import java.util.Properties;

public class EmailService {
    private final ConfigService.AppConfig config;

    public EmailService(ConfigService.AppConfig config) {
        this.config = config;
    }

    public void sendIfEnabled(String subject, String body) {
        if (!config.email().enabled()) return;
        try {
            Properties props = new Properties();
            props.put("mail.smtp.auth", "true");
            props.put("mail.smtp.starttls.enable", "true");
            props.put("mail.smtp.host", config.email().smtpHost());
            props.put("mail.smtp.port", String.valueOf(config.email().smtpPort()));
            Session session = Session.getInstance(props, new Authenticator() {
                @Override
                protected PasswordAuthentication getPasswordAuthentication() {
                    return new PasswordAuthentication(config.email().username(), config.email().password());
                }
            });
            Message msg = new MimeMessage(session);
            msg.setFrom(new InternetAddress(config.email().from()));
            for (String to : config.email().to()) {
                msg.addRecipient(Message.RecipientType.TO, new InternetAddress(to));
            }
            msg.setSubject(subject);
            msg.setText(body);
            Transport.send(msg);
        } catch (Exception e) {
            throw new RuntimeException("Email send failed: " + e.getMessage(), e);
        }
    }
}
