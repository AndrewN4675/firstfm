import axios from 'axios';


// Route to fetch data from django
const djangoRoute = axios.create({
    baseURL: 'http://localhost:8000/api/',
    withCredentials: true,
})

export default djangoRoute;