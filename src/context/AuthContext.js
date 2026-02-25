import React, { createContext, useState, useEffect, useCallback } from 'react';
import config from '../config';

export const AuthContext = createContext(null);

const BASE = config.API_BASE_URL;

async function fetchRefresh(refreshToken) {
    const res = await fetch(`${BASE}/auth/refresh`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${refreshToken}` },
    });
    if (!res.ok) throw new Error('Session expired');
    const { access_token } = await res.json();
    return access_token;
}

async function fetchMe(accessToken) {
    const res = await fetch(`${BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!res.ok) throw new Error('User not found');
    const { user } = await res.json();
    return user;
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [accessToken, setAccessToken] = useState(null);
    const [loading, setLoading] = useState(true);

    // On mount, restore session from stored refresh token
    useEffect(() => {
        async function restoreSession() {
            const stored = localStorage.getItem('refresh_token');
            if (!stored) {
                setLoading(false);
                return;
            }
            try {
                const token = await fetchRefresh(stored);
                const me = await fetchMe(token);
                setAccessToken(token);
                setUser(me);
            } catch {
                localStorage.removeItem('refresh_token');
            } finally {
                setLoading(false);
            }
        }
        restoreSession();
    }, []);

    const googleLogin = async (credential) => {
        const res = await fetch(`${BASE}/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credential }),
        });
        if (!res.ok) {
            const { error } = await res.json();
            throw new Error(error || 'Google sign-in failed');
        }
        const { access_token, refresh_token, user: me } = await res.json();
        setAccessToken(access_token);
        setUser(me);
        localStorage.setItem('refresh_token', refresh_token);
    };

    const impersonate = useCallback((access_token, impersonatedUser) => {
        setAccessToken(access_token);
        setUser(impersonatedUser);
    }, []);

    const logout = useCallback(() => {
        if (accessToken) {
            fetch(`${BASE}/auth/logout`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${accessToken}` },
            }).catch(() => {});
        }
        setAccessToken(null);
        setUser(null);
        localStorage.removeItem('refresh_token');
    }, [accessToken]);

    // Returns a valid access token, silently refreshing if the current one is gone.
    // Use this in any component making a protected API call.
    const getToken = useCallback(async () => {
        if (accessToken) return accessToken;
        const stored = localStorage.getItem('refresh_token');
        if (!stored) return null;
        try {
            const token = await fetchRefresh(stored);
            setAccessToken(token);
            return token;
        } catch {
            setAccessToken(null);
            setUser(null);
            localStorage.removeItem('refresh_token');
            return null;
        }
    }, [accessToken]);

    return (
        <AuthContext.Provider value={{ user, accessToken, loading, googleLogin, logout, getToken, impersonate }}>
            {children}
        </AuthContext.Provider>
    );
}
