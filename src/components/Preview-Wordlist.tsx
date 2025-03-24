import { StyleSheet, Text, View, Pressable } from 'react-native'
import { Word } from '../../assets/types/Word'
import {Link} from 'expo-router'

export const PreviewWordlist = ({ word }:{word : Word}) => {
  return (
    <Link asChild href={`/word/${word.name}`}>
        <Pressable style={styles.item}>
            <View style={styles.itemTextContainer}>
                <Text style={styles.itemTitle}>{word.name}</Text>
                <Text>{word.definition[word.partOfSpeech[0]].join("，")}</Text>
            </View>
        </Pressable>
    </Link>
  )
}

export default PreviewWordlist

const styles = StyleSheet.create({
    item: {
        width: '99%',
        backgroundColor: 'white',
        marginVertical: 8,
        borderRadius: 10,
        borderColor:"black",
        borderWidth:1,
        overflow: 'hidden',
      },
      itemTextContainer: {
        padding: 8,
        alignItems: 'flex-start',
        gap: 4,
      },
      itemTitle: {
        fontSize: 16,
        color: 'black',
      },
})