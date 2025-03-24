import { StyleSheet, Text, View, ScrollView, FlatList,TouchableOpacity } from 'react-native'
import { Redirect, useLocalSearchParams,Stack, } from 'expo-router'
import {useToast} from 'react-native-toast-notifications'
import {WORDS} from '../../../assets/constants/Words'
import { FontAwesome5 } from '@expo/vector-icons';

const WordDetail = () => {
    const{name} = useLocalSearchParams<{name:string}>()
    const toast = useToast();
    const word = WORDS.find(word => word.name === name)

    if(!word) return <Redirect href='/404'/>


  return (
    <View style={styles.container}>
      <Stack.Screen options= {{title: "Definition & Example" , headerTitleAlign: 'center',
        headerRight: () => (
          <TouchableOpacity
            onPress={() => alert("Button Pressed!")}
            style={{
              marginRight: 0,
              padding: 10,
              borderRadius: 5,
            }}
          >
            <FontAwesome5 name='edit' size={24} color='blue' />
          </TouchableOpacity>
        ),
      }}/>
      <ScrollView contentContainerStyle={styles.ScrollContainer} showsVerticalScrollIndicator={false}>
      <View style={{ padding: 16, flex: 1 }}>
        <Text style={styles.title}>{word.name}</Text>
        {word.partOfSpeech.map((part, index) => (
          <View key={index} style={{ marginBottom: 20}}>
            <Text style={styles.partOfSpeech}>{part}</Text>
            <Text style={styles.definition}>{word.definition[part].join('， ')}</Text>
            <View style={{ marginTop: 8 }}>
              {word.example[part].map((example, exampleIndex) => (
              <View key={exampleIndex}style={styles.bulletContainer}>
                <Text style={styles.bullet}>{'\u2022'}</Text>
                <Text key={exampleIndex} style={styles.example}>
                   {example}
                </Text>
              </View>
              ))}
            </View>
            {index < word.partOfSpeech.length - 1 && (
            <View style={{ height: 1, backgroundColor: 'purple', marginTop: 8 }} />)
            }
          </View>
        ))}
      </View> 
      </ScrollView>
      
    </View>
  )
}

export default WordDetail

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    title: {
        fontSize: 40,
        fontWeight: 'bold',
        marginBottom: 8,
    },
    partOfSpeech: {
      fontSize: 20,
      marginVertical: 8,
      color:"black",
      fontStyle: 'italic'
    },
    definition:{
    fontSize: 25,
    marginVertical: 8,
    color:"blue"
    },
    example:{
      fontSize: 20,
      marginVertical: 8,
      color:"black",
      },
    ScrollContainer: {
      padding: 10,
      backgroundColor: "white",
    },
    bulletContainer: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginBottom: 8,
    },
    bullet: {
      fontSize: 20,
      marginRight: 4,
      lineHeight: 45, 
    },
})