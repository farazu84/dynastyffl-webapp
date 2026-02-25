import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../hooks/useAuth';

export default function LoginModal({ onClose }) {
    const { googleLogin } = useAuth();
    const [error, setError] = useState('');

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal--compact" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>✕</button>
                <h2>Sign In</h2>
                <p className="modal-subtitle">Use your Google account to access the league.</p>
                {error && <p className="modal-error">{error}</p>}
                <div className="modal-google">
                    <GoogleLogin
                        onSuccess={async ({ credential }) => {
                            try {
                                await googleLogin(credential);
                                onClose();
                            } catch (err) {
                                setError(err.message);
                            }
                        }}
                        onError={() => setError('Google sign-in failed. Please try again.')}
                        theme="filled_black"
                        shape="rectangular"
                        size="large"
                        width="280"
                    />
                </div>
            </div>
        </div>
    );
}
