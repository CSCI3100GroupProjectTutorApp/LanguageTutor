// app/context/NetworkSyncProvider.tsx (Updated with translation event)

import React, { createContext, useState, useEffect, useContext, useCallback, useRef } from 'react';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as wordService from '../../src/services/wordService';
import { Alert, AppState, AppStateStatus, DeviceEventEmitter } from 'react-native';
import { useSegments, useRootNavigationState } from 'expo-router';

// Define the event name for translation completion
export const TRANSLATION_COMPLETED_EVENT = 'TRANSLATION_COMPLETED';

// Define the context type
type NetworkSyncContextType = {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: Date | null;
  syncAndTranslateWords: () => Promise<boolean>;
  translateWords: (userId: string) => Promise<boolean>;
};

// Create context with default values
const NetworkSyncContext = createContext<NetworkSyncContextType>({
  isOnline: false,
  isSyncing: false,
  lastSyncTime: null,
  syncAndTranslateWords: async () => false,
  translateWords: async () => false,
});

// Network & Sync Provider Component
export const NetworkSyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const previousConnectionState = useRef<boolean | null>(null);
  const syncLock = useRef<boolean>(false);
  const syncIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const appState = useRef<AppStateStatus>(AppState.currentState);
  
  // Get current route segments to check if we're in auth pages
  const segments = useSegments();
  const navigationState = useRootNavigationState();
  
  // Function to check if we're in auth pages
  const isInAuthPages = useCallback(() => {
    // Only check when navigation is ready
    if (!navigationState?.key) return true; // Default to true (don't sync) until we're certain
    
    // Check if first segment is in auth group
    return segments?.[0] === '(auths)';
  }, [segments, navigationState?.key]);
  
  // Load user ID
  useEffect(() => {
    const loadUserId = async () => {
      try {
        const id = await AsyncStorage.getItem("userid") || 
                  await AsyncStorage.getItem("userId");
        
        if (id) {
          console.log("Network sync provider loaded userId:", id);
          setUserId(id);
          
          // Check if we should trigger initial sync
          if (!isInAuthPages()) {
            const networkState = await NetInfo.fetch();
            const isConnected = !!networkState.isConnected && !!networkState.isInternetReachable;
            if (isConnected) {
              console.log("INITIAL SYNC: User ID loaded and device is online - triggering initial sync");
              // Slightly delay the initial sync to ensure everything is initialized
              setTimeout(() => {
                doSync(id);
              }, 2000);
            }
          } else {
            console.log("SYNC SKIPPED: In auth pages, skipping initial sync");
          }
        } else {
          console.warn("Network sync provider: No user ID found");
        }
      } catch (error) {
        console.error("Network sync provider failed to load user ID:", error);
      }
    };
    
    loadUserId();
  }, [isInAuthPages]);

  // Function to handle translation only
  const translateWords = useCallback(async (uid: string): Promise<boolean> => {
    if (!isOnline) {
      console.log("TRANSLATION SKIPPED: Device is offline");
      return false;
    }
    
    try {
      console.log("TRANSLATION STARTED: Processing translation queue");
      
      // Check if there are any words needing translation
      const db = await wordService.initDatabase(uid);
      const pendingTranslations = await db.getFirstAsync<{count: number}>(
        'SELECT COUNT(*) as count FROM words WHERE translated = 0'
      );
      
      if (!pendingTranslations || pendingTranslations.count === 0) {
        console.log("TRANSLATION SKIPPED: No pending translations");
        return true;
      }
      
      console.log(`TRANSLATION: Processing ${pendingTranslations.count} words`);
      
      // Process translations
      const success = await wordService.processTranslationQueue(uid);
      
      if (success) {
        console.log("TRANSLATION COMPLETED: Successfully translated words");
        
        // Emit event to notify components to reload data
        DeviceEventEmitter.emit(TRANSLATION_COMPLETED_EVENT);
        
        return true;
      } else {
        console.log("TRANSLATION FAILED: Issues during translation");
        return false;
      }
    } catch (error) {
      console.error("TRANSLATION ERROR:", error);
      return false;
    }
  }, [isOnline]);

  // Dedicated sync function for internal use
  const doSync = async (uid: string) => {
    // Check if we're in auth pages - skip sync
    if (isInAuthPages()) {
      console.log("SYNC SKIPPED: In auth pages, not allowed to sync");
      return false;
    }
    
    if (syncLock.current) {
      console.log("SYNC SKIPPED: Sync already in progress");
      return false;
    }
    
    try {
      syncLock.current = true;
      setIsSyncing(true);
      console.log("SYNC STARTED: Beginning sync operation");
      
      // First check if there's anything to sync - get pending counts
      const db = await wordService.initDatabase(uid);
      const operationsCount = await db.getFirstAsync<{count: number}>(
        'SELECT COUNT(*) as count FROM sync_queue'
      );
      const pendingTranslations = await db.getFirstAsync<{count: number}>(
        'SELECT COUNT(*) as count FROM words WHERE translated = 0'
      );
      
      // Only proceed if there's actual work to do
      if ((operationsCount && operationsCount.count > 0) || 
          (pendingTranslations && pendingTranslations.count > 0)) {
        
        console.log(`SYNC INFO: Found ${operationsCount?.count || 0} operations and ${pendingTranslations?.count || 0} pending translations`);
        
        // Process pending translations
        if (pendingTranslations && pendingTranslations.count > 0) {
          const translationSuccess = await wordService.processTranslationQueue(uid);
          
          if (translationSuccess) {
            // Emit event to notify components to reload data
            DeviceEventEmitter.emit(TRANSLATION_COMPLETED_EVENT);
          }
        }
        
        // Then sync with server
        if (operationsCount && operationsCount.count > 0) {
          const syncResult = await wordService.syncWithServer(uid);
          
          if (syncResult) {
            console.log("SYNC SUCCESS: Sync completed successfully");
            const now = new Date();
            setLastSyncTime(now);
            await AsyncStorage.setItem('lastSyncTime', now.toISOString());
            
            // Emit event to notify components to reload data
            DeviceEventEmitter.emit(TRANSLATION_COMPLETED_EVENT);
            
            return true;
          } else {
            console.log("SYNC FAILED: Sync completed with issues");
            return false;
          }
        } else {
          console.log("SYNC INFO: No operations to sync");
          return true;
        }
      } else {
        console.log("SYNC SKIPPED: No pending operations or translations");
        return true;
      }
    } catch (error) {
      console.error("SYNC ERROR:", error);
      return false;
    } finally {
      setIsSyncing(false);
      syncLock.current = false;
    }
  };

  // Public sync function
  const syncAndTranslateWords = useCallback(async (): Promise<boolean> => {
    // Check if we're in auth pages - skip sync
    if (isInAuthPages()) {
      console.log("MANUAL SYNC SKIPPED: In auth pages, not allowed to sync");
      return false;
    }
    
    if (!userId) {
      console.log("MANUAL SYNC SKIPPED: No user ID available");
      return false;
    }
    
    if (!isOnline) {
      console.log("MANUAL SYNC SKIPPED: Device is offline");
      return false;
    }
    
    console.log("MANUAL SYNC: Sync requested by user");
    return doSync(userId);
  }, [userId, isOnline, isInAuthPages]);
  
  // Setup periodic sync when online
  useEffect(() => {
    // Clear any existing interval
    if (syncIntervalRef.current) {
      clearInterval(syncIntervalRef.current);
      syncIntervalRef.current = null;
    }
    
    // Only set up periodic sync if we're online, have a user ID, and not in auth pages
    if (isOnline && userId && !isInAuthPages()) {
      console.log("PERIODIC SYNC: Setting up 1-minute sync interval");
      
      // Set up a new interval - sync every minute
      syncIntervalRef.current = setInterval(() => {
        console.log("PERIODIC SYNC: Interval triggered");
        
        // Double-check we're not in auth pages before syncing
        if (isInAuthPages()) {
          console.log("PERIODIC SYNC: In auth pages, skipping scheduled sync");
          return;
        }
        
        // Only sync if app is in foreground
        if (appState.current === 'active') {
          doSync(userId);
        } else {
          console.log("PERIODIC SYNC: App not active, skipping");
        }
      }, 30000); // 60000 ms = 1 minute
    }
    
    // Cleanup on unmount
    return () => {
      if (syncIntervalRef.current) {
        console.log("PERIODIC SYNC: Clearing sync interval");
        clearInterval(syncIntervalRef.current);
      }
    };
  }, [isOnline, userId, isInAuthPages]);
  
  // Monitor app state changes
  useEffect(() => {
    const subscription = AppState.addEventListener('change', nextAppState => {
      console.log(`App state changed from ${appState.current} to ${nextAppState}`);
      
      // If app comes to foreground and we're online, trigger sync - but not in auth pages
      if (appState.current.match(/inactive|background/) && 
          nextAppState === 'active' && 
          isOnline && 
          userId && 
          !isInAuthPages()) {
        console.log("APP FOREGROUND SYNC: App came to foreground, triggering sync");
        doSync(userId);
      }
      
      appState.current = nextAppState;
    });
    
    return () => {
      subscription.remove();
    };
  }, [isOnline, userId, isInAuthPages]);

  // Monitor navigation state changes to start/stop sync based on route
  useEffect(() => {
    // If we moved into auth pages, stop any sync activity
    if (isInAuthPages()) {
      console.log("NAVIGATION: Entered auth pages, stopping sync activities");
      
      // Clear any existing interval
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
        syncIntervalRef.current = null;
      }
    } 
    // If we moved out of auth pages and have necessary prerequisites, restart sync
    else if (userId && isOnline && navigationState?.key) {
      console.log("NAVIGATION: Exited auth pages, resuming sync activities");
      
      // Trigger immediate sync
      doSync(userId);
      
      // Set up periodic sync if not already running
      if (!syncIntervalRef.current) {
        console.log("NAVIGATION: Setting up sync interval after auth exit");
        syncIntervalRef.current = setInterval(() => {
          if (appState.current === 'active' && !isInAuthPages()) {
            doSync(userId);
          }
        }, 60000);
      }
    }
  }, [segments, navigationState?.key, userId, isOnline, isInAuthPages]);

  // Monitor network connectivity
  useEffect(() => {
    // Subscribe to network changes
    const unsubscribe = NetInfo.addEventListener(state => {
      const currentOnlineState = !!state.isConnected && !!state.isInternetReachable;
      const previousState = previousConnectionState.current;
      
      console.log(`NETWORK CHANGE: ${previousState === null ? 'Initial' : previousState ? 'Online→' : 'Offline→'}${currentOnlineState ? 'Online' : 'Offline'}`);
      
      setIsOnline(currentOnlineState);
      
      // If we just came online, have a user ID, were previously offline, and not in auth pages
      if (userId && currentOnlineState && previousState === false && !isInAuthPages()) {
        console.log("NETWORK RECOVERY SYNC: Device came online - triggering sync");
        doSync(userId).then(success => {
          if (success) {
            console.log("NETWORK RECOVERY SYNC: Completed successfully");
            Alert.alert('Sync Complete', 'Your data has been synchronized with the server.');
          } else {
            console.log("NETWORK RECOVERY SYNC: Failed");
          }
        });
      }
      
      // Update previous state
      previousConnectionState.current = currentOnlineState;
    });
    
    // Load last sync time
    const loadLastSyncTime = async () => {
      try {
        const timeStr = await AsyncStorage.getItem('lastSyncTime');
        if (timeStr) {
          setLastSyncTime(new Date(timeStr));
        }
      } catch (error) {
        console.error('Failed to load last sync time:', error);
      }
    };
    
    loadLastSyncTime();
    
    return () => {
      unsubscribe();
    };
  }, [userId, isInAuthPages]);

  // Context value
  const contextValue: NetworkSyncContextType = {
    isOnline,
    isSyncing,
    lastSyncTime,
    syncAndTranslateWords,
    translateWords
  };

  return (
    <NetworkSyncContext.Provider value={contextValue}>
      {children}
    </NetworkSyncContext.Provider>
  );
};

// Custom hook to use the network sync context
export const useNetworkSync = () => useContext(NetworkSyncContext);