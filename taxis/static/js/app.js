import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js';
import { getDatabase, ref, set, update } from 'https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js';


// Inicializa Firebase
const firebaseConfig = {
    apiKey: "AIzaSyB5howvle_Wt7cbIhx_BQ_VDu01yQaDcLM",
    authDomain: "jaidriver-828b5.firebaseapp.com",
    projectId: "jaidriver-828b5",
    storageBucket: "jaidriver-828b5.firebasestorage.app",
    messagingSenderId: "666937281439",
    appId: "1:666937281439:web:1979c4629dd5cfe1b90baa",
    measurementId: "G-TFYKX0NHHY"
};

// Inicializar la aplicación de Firebase
const app = initializeApp(firebaseConfig);

// Inicializar la base de datos
const database = getDatabase(app);

// Datos de la estructura completa
const webrtcData = {
    group1: {
        users: {
            user1: {
                id: "user1",
                isTalking: false
            },
            user2: {
                id: "user2",
                isTalking: false
            }
        },
        signaling: {
            offers: {
                user1: {
                    sdp: "offer-sdp-data",
                    type: "offer"
                }
            },
            answers: {
                user2: {
                    sdp: "answer-sdp-data",
                    type: "answer"
                }
            },
            iceCandidates: {
                user1: [
                    {
                        candidate: "candidate-data",
                        sdpMid: "0",
                        sdpMLineIndex: 0
                    }
                ]
            }
        }
    }
};

// Guardar toda la estructura en Firebase
set(ref(database, 'webrtc'), webrtcData)
    .then(() => {
        console.log("Estructura guardada correctamente.");
    })
    .catch((error) => {
        console.error("Error al guardar la estructura:", error);
    });
