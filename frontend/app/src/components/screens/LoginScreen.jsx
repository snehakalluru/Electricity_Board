import React, { useState } from "react";
import { Form, Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Messages from "../Messages";
import "./LoginScreen.css";

function LoginScreen() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [messageVariant, setMessageVariant] = useState("danger");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async(e) => {
    e.preventDefault();
    setMessage("");
    setIsSubmitting(true);

    try {
      const response = await axios.post("/login/", {
        username,
        password,
      });

      localStorage.setItem("userData", JSON.stringify(response.data));
      setMessageVariant("success");
      setMessage("Login successful");
      setUsername("");
      setPassword("");
      setTimeout(() => navigate("/"), 500);
      } catch (error) {
        setMessageVariant("danger");
        setMessage(error.response?.data?.error || "Login failed. Please try again.");
      } finally {
        setIsSubmitting(false);
      }
  };


  
  return (
    <main className="login-page">
      <div className="login-shell">
        <section className="login-brand" aria-label="Electricity Board">
          <div className="login-brand__mark">
            <img
              src="/electricity-logo.svg"
              alt=""
              className="login-brand__logo"
            />
          </div>
          <p className="login-brand__eyebrow">Admin Portal</p>
          <h1>Electricity Board</h1>
          <p>
            Secure access for reviewing connection requests, applicant records,
            and dashboard statistics.
          </p>
          <div className="login-brand__features" aria-label="Portal features">
            <span>Applicant records</span>
            <span>Connection status</span>
            <span>Monthly analytics</span>
          </div>
        </section>

        <section className="login-card">
          <div className="login-card__header">
            <h2>Sign In</h2>
            <p>Enter your username or email and password to continue.</p>
          </div>

          {message && <Messages variant={messageVariant}>{message}</Messages>}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="formBasicUsername">
              <Form.Label>Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="Username or email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-4" controlId="formBasicPassword">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </Form.Group>

            <Button variant="primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Signing In..." : "Login"}
            </Button>
            <p className="login-card__hint">
              Use the same credentials you use for the Django admin account.
            </p>
          </Form>
        </section>
      </div>
    </main>
  )
}

export default LoginScreen
