import React, { useState } from 'react';
import axios from 'axios';
import './styles.css'

function App() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [message, setMessage] = useState('');
    const [images, setImages] = useState([]);
    const [fileName, setSelectedFile1] = useState('Файл не выбран');
    const [feedback, setFeedback] = useState('');
    const [suggestion, setSuggestion] = useState('');
    //const fileChosen = document.getElementById('file-chosen');

    const submitFeedback = async () => {
        const response = await fetch("http://localhost:5000/feedback", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            feedback: feedback,
            suggestion: suggestion,
          }),
        });
    
        if (response.ok) {
          alert("Спасибо за вашу обратную связь!");
        } else {
          alert("Ошибка при отправке обратной связи.");
        }
    };

    const handleFileChange = (event) => {
        if (event.target.files.length > 0) {
            setSelectedFile(event.target.files[0]);
            setSelectedFile1(event.target.files[0]);
            console.log("Selected file:", event.target.files[0]);
        }
        
    };
   
    const handleUpload = async () => {
        if (!selectedFile) {
            setMessage('Please select a file');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await axios.post('http://localhost:5000/upload', formData);
            console.log(response.data);
            setMessage(response.data.message);
            fetchImages();
        } catch (error) {
            console.error('Error uploading file:', error);
            setMessage('Error uploading file');
        }
    };
    const fetchImages = async () => {
        try {
            const responce = await axios.get('http://localhost:5000/images');
            setImages(responce.data);
        } catch (error) {
            console.error('Error fetching images: ', error);
        }
    };

    return (
        <div>
            <h1>Загрузка изображения</h1>
            <input type="file" onChange={handleFileChange} id="actual-btn" hidden/>
            <label for="actual-btn">Выберите файл</label>
            <span id="file-chosen">{fileName.name}</span>
            <button onClick={handleUpload}>Загрузить</button>
            <button onClick={fetchImages}>Сгенерировать рецензию</button>
            <p>{message}</p>
            <h2>Загруженное изображение</h2>
            <ul>
                {images.map((image) => (
                    <li>
                        <img src={`data:image/jpg;base64,${image.image}`}
                        alt={image.name}
                        style={{width: '500px', height:'auto'}}
                        />
                        
                        <p class="get"><strong>{image.name}</strong></p>
                        <p class="get">{image.description}</p>
                        <p class="get">{image.rezenz}</p>
                    </li>
                ))}
            </ul>
            {images.map((image) => (
                <div>
                <h1>Обратная связь</h1>
                <label>
                  Оценка:
                  <select value={feedback} onChange={(e) => setFeedback(e.target.value)}>
                    <option value="">Выберите оценку</option>
                    <option value="1">1 - Плохо</option>
                    <option value="2">2 - Неудовлетворительно</option>
                    <option value="3">3 - Удовлетворительно</option>
                    <option value="4">4 - Хорошо</option>
                    <option value="5">5 - Отлично</option>
                  </select>
                </label>
                <br />
                <label>
                  Ваш комментарий:
                  <textarea
                    value={suggestion}
                    onChange={(e) => setSuggestion(e.target.value)}
                  ></textarea>
                </label>
                <br />
                <button onClick={submitFeedback}>Отправить</button>
              </div>
            ))}
        </div>
        
    );
}

export default App;
