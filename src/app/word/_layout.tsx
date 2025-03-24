import { Stack } from 'expo-router';
import { TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function WordLayout() {
  return (
    <Stack>
      <Stack.Screen
        name='[name]'
        options={({ navigation }) => ({
          headerShown: true,
          headerLeft: () => (
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name='arrow-back' size={24} color='black' />
            </TouchableOpacity>
          ),
        })}
      />
    </Stack>
  );
}