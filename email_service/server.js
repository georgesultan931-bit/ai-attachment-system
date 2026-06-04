const express = require("express");
const nodemailer = require("nodemailer");
const dotenv = require("dotenv");
const otpGenerator = require("otp-generator");
const cors = require("cors");

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());

const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 465,
    secure: true,
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
    },
    tls: {
        rejectUnauthorized: false,
    },
    connectionTimeout: 60000,
    greetingTimeout: 30000,
    socketTimeout: 60000,
});
app.get("/", (req, res) => {
    res.send("AI Internship Email Service Running");
});

app.post("/send-otp", async (req, res) => {

    try {

        const { email, username } = req.body;

        const otp = otpGenerator.generate(6, {
            upperCaseAlphabets: false,
            lowerCaseAlphabets: false,
            specialChars: false,
        });

        await transporter.sendMail({
            from: process.env.EMAIL_USER,
            to: email,
            subject: "OTP Verification",
            html: `
                <h2>AI Internship & Attachment System</h2>
                <p>Hello ${username}</p>
                <h1>${otp}</h1>
                <p>Your OTP verification code.</p>
            `,
        });

        return res.json({
            success: true,
            otp: otp,
        });

    } catch (error) {

        return res.status(500).json({
            success: false,
            error: error.message,
        });
    }
});

app.post("/send-email", async (req, res) => {

    try {

        const {
            email,
            subject,
            message
        } = req.body;

        await transporter.sendMail({
            from: process.env.EMAIL_USER,
            to: email,
            subject: subject,
            html: `
                <h2>AI Internship & Attachment System</h2>
                <p>${message}</p>
            `,
        });

        return res.json({
            success: true
        });

    } catch (error) {

        return res.status(500).json({
            success: false,
            error: error.message,
        });
    }
});

app.listen(process.env.PORT, () => {

    console.log(
        `Email service running on port ${process.env.PORT}`
    );

});