import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from datetime import datetime, timedelta
import os
import math

class SpatialNeighborService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpatialNeighborService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'final_master_dataset.csv')
        self.df = pd.read_csv(csv_path)
        self.df['Date'] = pd.to_datetime(self.df['Date']).dt.strftime('%Y-%m-%d')
        
        # Build station index
        self.stations = self.df[['Station', 'Latitude', 'Longitude']].drop_duplicates().reset_index(drop=True)
        
        # Convert to radians for haversine KDTree
        # cKDTree doesn't do haversine natively, but we can do 3D euclidean approximation or just use nearest neighbors and compute haversine accurately.
        coords_rad = np.radians(self.stations[['Latitude', 'Longitude']].values)
        
        # 3D Cartesian coordinates for KDTree (unit sphere)
        # x = cos(lat) * cos(lon)
        # y = cos(lat) * sin(lon)
        # z = sin(lat)
        x = np.cos(coords_rad[:, 0]) * np.cos(coords_rad[:, 1])
        y = np.cos(coords_rad[:, 0]) * np.sin(coords_rad[:, 1])
        z = np.sin(coords_rad[:, 0])
        self.tree = cKDTree(np.c_[x, y, z])
        
    def _haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371.0 * c
        
    def get_neighbors(self, latitude: float, longitude: float, date_str: str, target: str, k: int = 3):
        """
        Finds valid observations from OTHER stations only.
        Follows temporal fallback T, T-1, T-2, T-3.
        Never T+1.
        """
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # We need to find other stations.
        # Let's query the 3D KDTree for nearest stations
        lat_rad = math.radians(latitude)
        lon_rad = math.radians(longitude)
        qx = math.cos(lat_rad) * math.cos(lon_rad)
        qy = math.cos(lat_rad) * math.sin(lon_rad)
        qz = math.sin(lat_rad)
        
        # Query more neighbors than k to ensure we get enough valid ones
        dists, indices = self.tree.query([qx, qy, qz], k=len(self.stations))
        
        valid_neighbors = []
        
        # First, we must identify if the queried lat/lon corresponds to a station itself to exclude it!
        # If distance is extremely close (e.g. < 1km), it's the same station.
        
        for idx in indices:
            st = self.stations.iloc[idx]
            st_name = st['Station']
            st_lat = st['Latitude']
            st_lon = st['Longitude']
            
            dist_km = self._haversine(latitude, longitude, st_lat, st_lon)
            if dist_km < 1.0:
                continue # Skip self
                
            # Try to find a valid observation within [T-3, T]
            found = False
            for offset in range(4):
                search_date = (target_date - timedelta(days=offset)).strftime('%Y-%m-%d')
                
                # Look up in df
                row = self.df[(self.df['Station'] == st_name) & (self.df['Date'] == search_date)]
                if not row.empty:
                    val = row.iloc[0][target]
                    if pd.notna(val):
                        valid_neighbors.append({
                            'station': st_name,
                            'latitude': st_lat,
                            'longitude': st_lon,
                            'distance_km': dist_km,
                            'value': float(val),
                            'source_date': search_date,
                            'offset_days': offset,
                            'observed': True
                        })
                        found = True
                        break
                        
            if found and len(valid_neighbors) == k:
                break
                
        return valid_neighbors

# Singleton instance
spatial_neighbor_service = SpatialNeighborService()
