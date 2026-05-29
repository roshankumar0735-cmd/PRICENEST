import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
import {
  getAuth,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  signOut,
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyAPkMff4klSo28J-UIwjl6dXwpYzAc6nKM",
  authDomain: "pricenest-f43e2.firebaseapp.com",
  projectId: "pricenest-f43e2",
  storageBucket: "pricenest-f43e2.firebasestorage.app",
  messagingSenderId: "103035392754",
  appId: "1:103035392754:web:bac047e3e46062cc30f66b",
  measurementId: "G-P0F33B9FXS",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
auth.useDeviceLanguage();

window.pricenestFirebase = {
  app,
  auth,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  signOut,
};

window.dispatchEvent(new Event("pricenest-firebase-ready"));
