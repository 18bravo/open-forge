'use client';

/**
 * Learn View - Interactive learning modules with quizzes
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Clock, CheckCircle2, XCircle, ChevronRight, RotateCcw, Trophy } from 'lucide-react';
import { LEARNING_MODULES } from '../data';
import type { LearningModule, QuizQuestion } from '../types';

export function LearnView() {
  const [selectedModule, setSelectedModule] = useState<LearningModule | null>(null);
  const [quizMode, setQuizMode] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [showResults, setShowResults] = useState(false);

  const handleStartQuiz = () => {
    setQuizMode(true);
    setCurrentQuestion(0);
    setAnswers({});
    setShowResults(false);
  };

  const handleAnswer = (questionId: string, optionIndex: number) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionIndex }));
  };

  const handleNextQuestion = () => {
    if (selectedModule?.quiz && currentQuestion < selectedModule.quiz.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      setShowResults(true);
    }
  };

  const handleRestart = () => {
    setCurrentQuestion(0);
    setAnswers({});
    setShowResults(false);
  };

  const handleBackToModules = () => {
    setSelectedModule(null);
    setQuizMode(false);
    setShowResults(false);
  };

  const calculateScore = () => {
    if (!selectedModule?.quiz) return 0;
    let correct = 0;
    selectedModule.quiz.forEach(q => {
      if (answers[q.id] === q.correctIndex) correct++;
    });
    return correct;
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 overflow-y-auto">
      <div className="max-w-4xl mx-auto p-8">
        <AnimatePresence mode="wait">
          {!selectedModule ? (
            // Module Selection
            <motion.div
              key="modules"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-white mb-2">Learning Modules</h2>
                <p className="text-slate-400">Master defense enterprise concepts through interactive lessons</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {LEARNING_MODULES.map((module, index) => (
                  <motion.button
                    key={module.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => setSelectedModule(module)}
                    className="p-6 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 rounded-xl text-left transition-all group"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors">
                        <BookOpen className="w-6 h-6 text-blue-400" />
                      </div>
                      <div className="flex items-center gap-1 text-slate-500">
                        <Clock className="w-4 h-4" />
                        <span className="text-sm">{module.duration}</span>
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                      {module.title}
                    </h3>
                    <p className="text-sm text-slate-400 mb-4">{module.description}</p>

                    <div className="flex flex-wrap gap-2">
                      {module.topics.slice(0, 3).map((topic, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-slate-700/50 rounded text-xs text-slate-400"
                        >
                          {topic}
                        </span>
                      ))}
                      {module.topics.length > 3 && (
                        <span className="px-2 py-1 text-xs text-slate-500">
                          +{module.topics.length - 3} more
                        </span>
                      )}
                    </div>

                    {module.quiz && (
                      <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center gap-2 text-slate-500">
                        <Trophy className="w-4 h-4" />
                        <span className="text-sm">{module.quiz.length} quiz questions</span>
                      </div>
                    )}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          ) : !quizMode ? (
            // Module Content
            <motion.div
              key="content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <button
                onClick={handleBackToModules}
                className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
              >
                <ChevronRight className="w-4 h-4 rotate-180" />
                Back to modules
              </button>

              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">{selectedModule.title}</h2>
                    <p className="text-slate-400">{selectedModule.description}</p>
                  </div>
                  <div className="flex items-center gap-1 text-slate-500">
                    <Clock className="w-4 h-4" />
                    <span>{selectedModule.duration}</span>
                  </div>
                </div>

                <div className="mb-8">
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                    Topics Covered
                  </h3>
                  <ul className="space-y-3">
                    {selectedModule.topics.map((topic, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-xs font-semibold text-blue-400">{i + 1}</span>
                        </div>
                        <span className="text-slate-300">{topic}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {selectedModule.quiz && (
                  <button
                    onClick={handleStartQuiz}
                    className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2"
                  >
                    <Trophy className="w-5 h-5" />
                    Take the Quiz ({selectedModule.quiz.length} questions)
                  </button>
                )}
              </div>
            </motion.div>
          ) : showResults ? (
            // Quiz Results
            <motion.div
              key="results"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8 text-center">
                <div className="mb-6">
                  {calculateScore() === selectedModule.quiz?.length ? (
                    <div className="w-20 h-20 mx-auto bg-green-500/20 rounded-full flex items-center justify-center mb-4">
                      <Trophy className="w-10 h-10 text-green-400" />
                    </div>
                  ) : calculateScore() >= (selectedModule.quiz?.length || 0) / 2 ? (
                    <div className="w-20 h-20 mx-auto bg-blue-500/20 rounded-full flex items-center justify-center mb-4">
                      <CheckCircle2 className="w-10 h-10 text-blue-400" />
                    </div>
                  ) : (
                    <div className="w-20 h-20 mx-auto bg-amber-500/20 rounded-full flex items-center justify-center mb-4">
                      <RotateCcw className="w-10 h-10 text-amber-400" />
                    </div>
                  )}

                  <h2 className="text-2xl font-bold text-white mb-2">Quiz Complete!</h2>
                  <p className="text-4xl font-bold text-white mb-2">
                    {calculateScore()} / {selectedModule.quiz?.length}
                  </p>
                  <p className="text-slate-400">
                    {calculateScore() === selectedModule.quiz?.length
                      ? 'Perfect score! Outstanding!'
                      : calculateScore() >= (selectedModule.quiz?.length || 0) / 2
                      ? 'Good job! Keep learning!'
                      : 'Review the material and try again!'}
                  </p>
                </div>

                {/* Answer Review */}
                <div className="text-left mb-6">
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                    Answer Review
                  </h3>
                  <div className="space-y-4">
                    {selectedModule.quiz?.map((q, i) => (
                      <div
                        key={q.id}
                        className={`p-4 rounded-lg border ${
                          answers[q.id] === q.correctIndex
                            ? 'bg-green-500/10 border-green-500/30'
                            : 'bg-red-500/10 border-red-500/30'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {answers[q.id] === q.correctIndex ? (
                            <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                          )}
                          <div>
                            <p className="text-sm text-white font-medium mb-1">
                              Q{i + 1}: {q.question}
                            </p>
                            <p className="text-xs text-slate-400">
                              Correct: {q.options[q.correctIndex]}
                            </p>
                            {answers[q.id] !== q.correctIndex && (
                              <p className="text-xs text-slate-500 mt-1">
                                {q.explanation}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handleRestart}
                    className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
                  >
                    Try Again
                  </button>
                  <button
                    onClick={handleBackToModules}
                    className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors"
                  >
                    Back to Modules
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            // Quiz Questions
            <QuizView
              module={selectedModule}
              currentQuestion={currentQuestion}
              answers={answers}
              onAnswer={handleAnswer}
              onNext={handleNextQuestion}
              onBack={handleBackToModules}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

interface QuizViewProps {
  module: LearningModule;
  currentQuestion: number;
  answers: Record<string, number>;
  onAnswer: (questionId: string, optionIndex: number) => void;
  onNext: () => void;
  onBack: () => void;
}

function QuizView({ module, currentQuestion, answers, onAnswer, onNext, onBack }: QuizViewProps) {
  const question = module.quiz?.[currentQuestion];
  if (!question) return null;

  const hasAnswered = answers[question.id] !== undefined;

  return (
    <motion.div
      key={`question-${currentQuestion}`}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
    >
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <ChevronRight className="w-4 h-4 rotate-180" />
        Exit quiz
      </button>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
        {/* Progress */}
        <div className="flex items-center justify-between mb-6">
          <span className="text-sm text-slate-400">
            Question {currentQuestion + 1} of {module.quiz?.length}
          </span>
          <div className="flex gap-1">
            {module.quiz?.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full ${
                  i === currentQuestion
                    ? 'bg-blue-500'
                    : i < currentQuestion
                    ? 'bg-green-500'
                    : 'bg-slate-600'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Question */}
        <h2 className="text-xl font-semibold text-white mb-6">{question.question}</h2>

        {/* Options */}
        <div className="space-y-3 mb-6">
          {question.options.map((option, i) => {
            const isSelected = answers[question.id] === i;
            const isCorrect = hasAnswered && i === question.correctIndex;
            const isWrong = hasAnswered && isSelected && i !== question.correctIndex;

            return (
              <button
                key={i}
                onClick={() => !hasAnswered && onAnswer(question.id, i)}
                disabled={hasAnswered}
                className={`
                  w-full p-4 rounded-lg border text-left transition-all
                  ${!hasAnswered && 'hover:bg-slate-700/50 hover:border-slate-600'}
                  ${isSelected && !hasAnswered && 'bg-blue-500/20 border-blue-500'}
                  ${isCorrect && 'bg-green-500/20 border-green-500'}
                  ${isWrong && 'bg-red-500/20 border-red-500'}
                  ${!isSelected && !isCorrect && 'border-slate-700'}
                `}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`
                      w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0
                      ${isCorrect && 'bg-green-500 border-green-500'}
                      ${isWrong && 'bg-red-500 border-red-500'}
                      ${isSelected && !hasAnswered && 'bg-blue-500 border-blue-500'}
                      ${!isSelected && !isCorrect && !isWrong && 'border-slate-600'}
                    `}
                  >
                    {isCorrect && <CheckCircle2 className="w-4 h-4 text-white" />}
                    {isWrong && <XCircle className="w-4 h-4 text-white" />}
                  </div>
                  <span className="text-slate-200">{option}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Explanation */}
        {hasAnswered && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="p-4 bg-slate-700/30 rounded-lg mb-6"
          >
            <p className="text-sm text-slate-300">{question.explanation}</p>
          </motion.div>
        )}

        {/* Next button */}
        <button
          onClick={onNext}
          disabled={!hasAnswered}
          className={`
            w-full py-3 font-medium rounded-lg transition-all
            ${hasAnswered
              ? 'bg-blue-600 hover:bg-blue-500 text-white'
              : 'bg-slate-700 text-slate-500 cursor-not-allowed'
            }
          `}
        >
          {currentQuestion < (module.quiz?.length || 0) - 1 ? 'Next Question' : 'See Results'}
        </button>
      </div>
    </motion.div>
  );
}
