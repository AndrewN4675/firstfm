import axios from 'axios';

// Route to fetch data from django
const djangoRoute = axios.create({
    baseURL: `${process.env.NEXT_PUBLIC_BASE_ROUTE}/api`,
    withCredentials: true,
})

export default djangoRoute;