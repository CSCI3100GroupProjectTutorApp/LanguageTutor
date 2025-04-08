import fetchMock from "fetch-mock";

fetchMock.post("http://localhost:8000/extract-text", { text: "mock extracted text" });
fetchMock.post("http://localhost:8000/words", { word_id: "mock_word_id" });
fetchMock.get("http://localhost:8000/words", [{ text: "hello", translation: "hola", notes: "Spanish greeting" }]);