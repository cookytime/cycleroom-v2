import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Stage, Layer, Circle, Text, Line } from 'react-konva';

const RaceVisualization = () => {
    const [bikes, setBikes] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/bikes');
                setBikes(Object.entries(response.data));
            } catch (error) {
                console.error('Error fetching bike data:', error);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-4">Race Visualization</h1>
            <Stage width={800} height={400} className="border-2 border-gray-400">
                <Layer>
                    {/* Draw a simple oval racetrack */}
                    <Line
                        points={[100, 200, 700, 200, 700, 250, 100, 250]}
                        closed
                        stroke="black"
                        strokeWidth={4}
                        lineCap="round"
                        lineJoin="round"
                    />
                    {bikes.map(([bikeId, data], index) => (
                        <React.Fragment key={bikeId}>
                            <Circle
                                x={100 + (600 * (data.distance % 1))}
                                y={225}
                                radius={10}
                                fill="blue"
                            />
                            <Text
                                x={100 + (600 * (data.distance % 1))}
                                y={240}
                                text={`${bikeId}: ${data.distance.toFixed(2)}m`}
                                fontSize={12}
                                fill="black"
                            />
                        </React.Fragment>
                    ))}
                </Layer>
            </Stage>
        </div>
    );
};

export default RaceVisualization;
