
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const App = () => {
    const [bikeData, setBikeData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/bikes');
                const data = Object.entries(response.data).map(([key, value]) => ({
                    bike: key,
                    distance: value.distance
                }));
                setBikeData(data);
            } catch (error) {
                console.error('Error fetching bike data:', error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center">
            <h1 className="text-4xl font-bold text-gray-800 mb-6">Bike Race Visualization</h1>
            <div className="bg-white rounded-lg shadow-md p-6 w-11/12 md:w-3/4 lg:w-1/2">
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={bikeData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="bike" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="distance" stroke="#8884d8" activeDot={{ r: 8 }} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default App;
