import { useState, useEffect } from 'react';
import config from './config';

const Content = () => {
    const [name, setName] = useState('Faraz')
    const [user, setUser] = useState({});

  useEffect(() => {
    fetch(`${config.API_BASE_URL}/user/1`).then(res => res.json()).then(data => {
      console.log(data)
      setUser(data.user);
    });
  }, []);
    const handleClick = () => {
        console.log('Sup Dude');
    }
    const handleClick2 = (name) => {
        console.log(name);
    }
    return (
        <main>
            <p>Welcome {user.first_name} {user.last_name}</p>
        </main>
    )
}

export default Content