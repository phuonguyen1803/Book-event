let selectedSeats = [];

function selectSeat(seatId) {
    if (selectedSeats.includes(seatId)) {
        // Bỏ chọn ghế
        selectedSeats = selectedSeats.filter(id => id !== seatId);
        document.querySelector(`[data-seat-id="${seatId}"]`).classList.remove("selected");
    } else {
        // Chọn ghế
        selectedSeats.push(seatId);
        document.querySelector(`[data-seat-id="${seatId}"]`).classList.add("selected");
    }
    updateSelectedSeatsInfo();
}

function updateSelectedSeatsInfo() {
    const selectedSeatsList = document.getElementById("selected-seats-list");
    selectedSeatsList.innerHTML = '';
    selectedSeats.forEach(seat => {
        const li = document.createElement("li");
        li.innerText = `Ghế: ${seat}`;
        selectedSeatsList.appendChild(li);
    });
}

function confirmBooking() {
    fetch('/book_seat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ seats: selectedSeats }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        selectedSeats = [];  // Reset ghế đã chọn
        updateSelectedSeatsInfo();
    })
    .catch(error => console.error('Lỗi:', error));
    function submitSelection() {
    let selection = {
        event1: parseInt(document.getElementById('event1').value),
        event2: parseInt(document.getElementById('event2').value),
        event3: parseInt(document.getElementById('event3').value)
    };

    fetch('/submit_selection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(selection)
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error('Error:', error));
}

}