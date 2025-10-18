'use client';
import React, {useEffect, useState} from 'react'
import { fetchUserInfo } from '../services/page'

interface Username {
    username: string,
}


// Fetch username to confirm login link
export default function Dashboard() {
    const [username, setUsername] = useState<Username>();

    const getUserInfo = async () => {
        const response = await fetchUserInfo();
        setUsername(response);
    }

    useEffect(() => {
        getUserInfo();
    }, []);

  return (
    <div>Welcome: {username?.username}</div>
  )
}
