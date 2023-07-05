<template>
  <v-container fluid class="viewport">
    <div class="chat-area">
      <transition v-for="(item, idx) of history" :key="idx" name="fade-in-bottom">
        <chat-item class="fade-in-bottom" appear :text="item.text" :type="item.type"></chat-item>
      </transition>
    </div>
    <div class="guidance-links-container">
      <div v-if="(guidanceDocs|| []).length > 0" class="guidance-links-title">Relevant source materials</div>
      <v-card class="guidance-card" v-for="item of guidanceDocs" :key="item.key">
        <div class="guidance-card-title">{{item.title}}</div>
        <div class="guidance-card-content">
          {{item.content}}
        </div>
        <div class="guidance-link">
          <a :href="item.link" target="_blank">
            {{item.link}}
          </a>
        </div>
      </v-card>
    </div>
  </v-container>
  <v-container fluid class="question-box-container">
    <v-row>
      <v-col cols="11">
        <v-text-field
            v-model="message"
            label="Ask a question"
            outlined
            full-width
        ></v-text-field>
      </v-col>
      <v-col cols="1">
        <v-btn color="primary" @click="submitMessage">
          <v-icon icon="mdi-send"></v-icon>
        </v-btn>
        <v-dialog v-model="promptDialog" width="auto">
          <template v-slot:activator="{ props }">
            <v-btn @click="retrievePrompt" v-bind="props">
              <v-icon icon="mdi-bug"></v-icon>
            </v-btn>
          </template>
          <v-card>
            <v-text-area model-value="prompt">
            </v-text-area>
          </v-card>
          <v-btn @click="promptDialog = false"></v-btn>
        </v-dialog>

      </v-col>
    </v-row>
  </v-container>

</template>

<script lang="ts">
import axios from "axios";
import ChatItem from '../components/ChatItem.vue'

export default {
  name: 'HomeView',
  components: { ChatItem },
  data () {
    return {
      history: [],
      message: '',
      guidanceDocs: [],
      answer: '',
      prompt: null,
      promptDialog: false,
    }
  },
  methods: {
    submitMessage () {
      axios.post('/api/qa/', {query_str: this.message}).then(resp => {
        this.history.splice(0, this.history.length)
        this.history.push({
          type: 'human',
          text: this.message
        })
        this.history.push({
          type: 'AI',
          text: resp.data.answer.split('[STOP]')[0]
        })
        this.message = ''
        this.guidanceDocs = resp.data.sources.map(srcDoc => {
          return {
            content: srcDoc.content,
            title: srcDoc.title,
            key: srcDoc.source.split('/').slice(-1)[0],
            link: srcDoc.link,
            fullSource: srcDoc.full_source
          }
        })

        this.answer = resp.data.answer
      })
    },
    retrievePrompt () {
      axios.post('/api/gen-prompt/', {query_str: this.message}).then(resp => {
        this.prompt = resp.data.prompt
        this.promptDialog = true
      })
    }
  }
}
</script>

<style scoped>
.viewport {
  display: grid;
  grid-template-rows: 400px 1fr;
  grid-template-columns: 1fr;
  height: calc(100vh - 400px - 70px);
}
.chat-area {
  overflow-y: auto;
}
.guidance-links-container {
  height: calc(100vh - 400px - 200px);  /* 100% screen height minus 'chat' height  - top & bottom bars. */
  overflow-y: auto;
  text-align: center;
  margin: auto;
  box-shadow: rgba(0, 0, 0, 0.45) 0 15px 20px -25px
}

.guidance-card {
  max-height: 200px;
  /*height: 200px;*/
  max-width: 350px;
  display: inline-block;
  padding: 5px;
  margin: 10px;
  border-radius: var(--border-radius);
  box-shadow: rgba(0, 0, 0, 0.35) 0 5px 15px;
  color: var(--vt-c-text-light-2);
  overflow-y: auto;
}

.guidance-link {
  color: blue;
}

.guidance-links-title {
  box-shadow: rgba(0, 0, 0, 0.45) 0 15px 20px -25px;
  text-align: left;
  font-size: 22px;
}

.guidance-card-title {
  color: var(--color-heading);
  padding-bottom: 5px;
}

.guidance-card-content {
  /*max-height: 150px;*/
  /*overflow-y: auto;*/
}

.question-box-container {
  padding: 10px 15px;
  border: 1px solid var(--vt-c-black-soft);
  border-radius: var(--border-radius);
}

.fade-in-bottom-enter-active {
  transition: transform 0.5s ease;
}

.fade-in-bottom-enter {
  transform: translateY(100%);
}

.fade-in-bottom-leave-active {
  transition: transform 0.5s ease;
}

.fade-in-bottom-leave-to {
  transform: translateY(100%);
}

.fade-in-bottom {
  position: relative;
}

</style>
