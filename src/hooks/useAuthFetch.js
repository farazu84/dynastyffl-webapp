import { useCallback } from 'react';
import { useAuth } from './useAuth';
import config from '../config';

export function useAuthFetch() {
    const { getToken, logout } = useAuth();

    const authFetch = useCallback(async (path, options = {}) => {
        const token = await getToken();

        const res = await fetch(`${config.API_BASE_URL}${path}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
        });

        if (res.status === 401) {
            logout();
            throw new Error('Session expired. Please log in again.');
        }

        return res;
    }, [getToken, logout]);

    return authFetch;
}
