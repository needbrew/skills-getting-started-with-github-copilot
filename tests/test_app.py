"""Tests for the Mergington High School API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Clear participants from all activities
    for activity in activities.values():
        activity["participants"].clear()
    
    # Reset Chess Club and Programming Class with their initial participants
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]
    
    yield


class TestGetActivities:
    """Test cases for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Basketball Team" in data
        assert "Soccer Club" in data
        assert "Drama Club" in data
    
    def test_get_activities_contains_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Basketball Team"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_contains_existing_participants(self, client):
        """Test that activities include existing participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up student@mergington.edu for Basketball Team"
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        email = "student@mergington.edu"
        client.post(f"/activities/Basketball Team/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Team"]["participants"]
    
    def test_signup_duplicate_fails(self, client):
        """Test that signing up twice fails"""
        email = "student@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Basketball Team/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Basketball Team/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup for nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_multiple_participants(self, client):
        """Test that multiple participants can sign up"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(f"/activities/Soccer Club/signup?email={email}")
            assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data["Soccer Club"]["participants"]


class TestUnregisterFromActivity:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-participant fails"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from nonexistent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_after_signup(self, client):
        """Test unregistering after signing up"""
        email = "student@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Drama Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Drama Club/unregister?email={email}")
        
        # Verify unregistration
        response = client.get("/activities")
        assert email not in response.json()["Drama Club"]["participants"]


class TestRoot:
    """Test cases for GET / endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
